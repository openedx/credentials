import datetime
import logging
import textwrap
from itertools import groupby

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from edx_ace import Recipient, ace

from credentials.apps.catalog.data import ProgramStatus
from credentials.apps.core.api import get_user_by_username
from credentials.apps.credentials.messages import ProgramCertificateIssuedMessage
from credentials.apps.credentials.models import (
    ProgramCompletionEmailConfiguration,
    UserCredential,
    UserCredentialAttribute,
)


log = logging.getLogger(__name__)

VISIBLE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def to_language(locale):
    if locale is None:
        return None
    # Convert to bytes to get ascii-lowercasing, to avoid the Turkish I problem.
    return locale.replace("_", "-").encode().lower().decode()


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
        attributes (list): List of dicts contains attributes data

    Returns:
        Boolean: Return True only if data has no duplicated namespace and name

    """

    def keyfunc(attribute):
        return attribute["name"]

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True


def datetime_from_visible_date(date):
    """Turn a string version of a datetime, provided to us by the LMS in a particular format it uses for
    visible_date attributes, and turn it into a datetime object."""
    try:
        parsed = datetime.datetime.strptime(date, VISIBLE_DATE_FORMAT)
        # The timezone is always UTC (as indicated by the Z). It looks like in python3.7, we could
        # just use %z instead of replacing the tzinfo with a UTC value.
        return parsed.replace(tzinfo=datetime.timezone.utc)
    except ValueError as e:
        log.exception("%s", e)
        return None


# TODO: Refactor this when removing USE_CERTIFICATE_AVAILABLE_DATE toggle:
# MICROBA-1198
def filter_visible(qs):
    """
    Filters a UserCredentials queryset by excluding credentials that aren't
    supposed to be visible yet.
    """

    if settings.USE_CERTIFICATE_AVAILABLE_DATE.is_enabled():
        visible_course_certs = _filter_visible_course_certificates(qs.filter(course_credentials__isnull=False))
        visible_program_certs = _filter_visible_program_certificates(qs.filter(program_credentials__isnull=False))
        visible_certs = visible_course_certs | visible_program_certs

        return visible_certs

    # The visible_date attribute holds a string value, not a datetime one. But we can compare as a string
    # because the format is so strict - it will still lexically compare as less/greater-than.
    nowstr = datetime.datetime.now(datetime.timezone.utc).strftime(VISIBLE_DATE_FORMAT)
    return qs.filter(
        Q(attributes__name="visible_date", attributes__value__lte=nowstr) | ~Q(attributes__name="visible_date")
    )


def _filter_visible_course_certificates(query_set):
    """
    Filters a UserCredentials queryset by excluding credentials that aren’t
    supposed to be visible yet according to their certificate_available_date.

    Arguments:
        query_set (UserCredential QuerySet): A queryset of UserCredential objects of
        the CourseCertificate ContentType.

    Returns:
        (QuerySet): A queryset of course UserCredentials that should be visible.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    return query_set.filter(
        Q(course_credentials__certificate_available_date__lte=now)
        | Q(course_credentials__certificate_available_date__isnull=True)
    )


def _filter_visible_program_certificates(query_set):
    """
    Filters a UserCredentials queryset by excluding credentials that aren’t
    supposed to be visible yet according to their certificate_available_date.

    Arguments:
        query_set (UserCredential QuerySet): A queryset of UserCredential
        objects of the ProgramCertificate ContentType.

    Returns:
        (QuerySet): A queryset of program UserCredentials that should be visible.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    visible_program_cert_ids = []
    for user_credential in query_set:
        program_visible_date = _get_program_certificate_visible_date(user_credential)
        if program_visible_date and program_visible_date <= now:
            visible_program_cert_ids.append(user_credential.id)
    return UserCredential.objects.filter(pk__in=visible_program_cert_ids)


def _get_program_certificate_visible_date(user_program_credential):
    """
    Finds the program credential visible date by finding the latest associated
    course certificate_available_date. If a course credential has no
    certificate_available_date, use its created date instead.

    Arguments:
        user_program_credential (UserCredential): A single UserCredential object; this
        must be of the ProgramCertificate ContentType.

    Returns:
        (DateTime or None): The date on which the program credential should be
        visible. (It shouldn’t return None but is technically possible.)
    """
    last_date = None
    for course_run in user_program_credential.credential.program.course_runs.all():
        # Does the user have a course cert for this course run?
        course_run_cert = UserCredential.objects.filter(
            username=user_program_credential.username,
            course_credentials__course_run=course_run,
        ).first()

        if course_run_cert:
            date = _get_issue_date_for_course_credential(course_run_cert)
            last_date = max(last_date, date) if last_date else date

    return last_date


def _get_issue_date_for_course_credential(course_run_user_credentials):
    """
    Retrieves the issue date for a given course run UserCredential. This method
    attempts to find the date based on the certificate availability date and
    the visible date attribute.

    Arguments:
        course_run_user_credentials (UserCredential): A Course Run UserCredential

    Returns:
        datetime: The datetime that the credential should be visible and was issued.
    """
    if course_run_user_credentials.credential.certificate_available_date:
        date = course_run_user_credentials.credential.certificate_available_date
    else:
        try:
            visible_date = UserCredentialAttribute.objects.prefetch_related("user_credential__credential").get(
                user_credential=course_run_user_credentials, name="visible_date"
            )
            date = datetime_from_visible_date(visible_date.value)
        except UserCredentialAttribute.DoesNotExist:
            date = course_run_user_credentials.created
            log.info(f"UserCredential {course_run_user_credentials.id} does not have a visible_date attribute")
    return date


# TODO: Refactor this when removing USE_CERTIFICATE_AVAILABLE_DATE toggle:
# MICROBA-1198
def get_credential_visible_dates(user_credentials, use_date_override=False):
    """
    Calculates visible date for a collection of UserCredentials.
    Returns a dictionary of {UserCredential: datetime}.

    Pass True as the `use_date_override` parameter to override the normal
    visible date calculations with the UserCredential’s date override,
    if present.

    Returns:
        (Dict): Returns a dictionary of DateTimes keyed by UserCredential. If the
        credential's visible date cannot be calculated, returns None instead of
        a DateTime. Example:
            {
                <UserCredential>: <DateTime>,
                <UserCredential>: None,
                ...
            }
    """

    if settings.USE_CERTIFICATE_AVAILABLE_DATE.is_enabled():
        visible_date_dict = {}

        for user_credential in user_credentials:
            date = None
            # If this is a course credential
            if user_credential.course_credentials.exists():
                date = _get_issue_date_for_course_credential(user_credential)

                # Date override only applies to Course Run UserCredential dates
                # we should reconsider this if we ever decide they should
                # impact the issue date of Program Certs.
                if use_date_override:
                    try:
                        date = user_credential.date_override.date
                    except ObjectDoesNotExist:
                        pass

            # If this is a program credential
            if user_credential.program_credentials.exists():
                date = _get_program_certificate_visible_date(user_credential)

            visible_date_dict[user_credential] = date

        return visible_date_dict

    visible_dates = UserCredentialAttribute.objects.prefetch_related("user_credential__credential").filter(
        user_credential__in=user_credentials, name="visible_date"
    )

    visible_date_dict = {
        visible_date.user_credential: datetime_from_visible_date(visible_date.value) for visible_date in visible_dates
    }

    for user_credential in user_credentials:
        current = visible_date_dict.get(user_credential)
        if current is None:
            visible_date_dict[user_credential] = user_credential.created

    return visible_date_dict


def get_credential_visible_date(user_credential, use_date_override=False):
    """Simpler, one-credential version of get_credential_visible_dates."""
    return get_credential_visible_dates([user_credential], use_date_override)[user_credential]


def send_program_certificate_created_message(username, program_certificate, lms_user_id):
    """
    If the learner has earned a Program Certificate then we go ahead and send them an automated email congratulating
    them for their achievement. Emails to learners in credit eligible Programs will contain additional information.

    Args:
        username (string): The username of the user we will send the email to
        program_certificate (AbstractCredential[ProgramCertificate]): A ProgramCertificate configuration for a program,
         used to pull program details used in the program completion email
        lms_user_id (int): The LMS User Id of the user we will send the email to
    """
    user = get_user_by_username(username)
    program_uuid = program_certificate.program_uuid
    program_details = program_certificate.program_details

    email_configuration = ProgramCompletionEmailConfiguration.get_email_config_for_program(
        program_uuid, program_details.type_slug
    )
    # If a config doesn't exist or isn't enabled, we don't want to send emails for this program.
    if not getattr(email_configuration, "enabled", None):
        log.info(
            f"Not sending program completion email to learner [{user.id}] "
            f"in program [{program_uuid}] because it's not enabled"
        )
        return

    # Don't send out emails for retired programs
    if program_details.status == ProgramStatus.RETIRED.value:
        return

    try:
        if not lms_user_id:
            log.warning("Program certificate created email sent without lms_user_id")
        msg = ProgramCertificateIssuedMessage(program_certificate.site, user.email).personalize(
            recipient=Recipient(lms_user_id=lms_user_id, email_address=user.email),
            language=program_certificate.language,
            user_context={
                "program_title": program_details.title,
                "program_type": program_details.type,
                "custom_email_html_template_extra": email_configuration.html_template,
                # remove any leading spaces of the plaintext content so that the email doesn't look horrendous
                "custom_email_plaintext_template_extra": textwrap.dedent(email_configuration.plaintext_template),
                "logo_url": getattr(settings, "LOGO_URL_PNG", ""),
            },
        )
        log.info(f"Sending Program completion email to learner with id [{user.id}] in Program [{program_uuid}]")
        ace.send(msg)
    # We wouldn't want any issues that arise from formatting or sending this email message to interrupt the process
    # of issuing a learner their Program Certificate. We cast a wide net for exceptions here for this reason.
    except Exception as ex:
        log.exception(
            f"Unable to send email to learner with id: [{user.id}] for Program [{program_uuid}]. "
            f"Error occurred while attempting to format or send message: {ex}"
        )
