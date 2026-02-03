import datetime
import logging
import textwrap
from itertools import groupby
from typing import TYPE_CHECKING, Dict, Optional

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from edx_ace import Recipient, ace

from credentials.apps.catalog.data import ProgramStatus
from credentials.apps.core.api import get_user_by_username
from credentials.apps.credentials.messages import ProgramCertificateIssuedMessage
from credentials.apps.credentials.models import ProgramCompletionEmailConfiguration, UserCredential

if TYPE_CHECKING:
    from django.db.models import DateTimeField
    from django.db.models.query import QuerySet

    from credentials.apps.credentials.models import ProgramCertificate

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


def filter_visible(qs: "QuerySet") -> "QuerySet":
    """
    Filters a UserCredentials queryset by excluding credentials that aren't
    supposed to be visible yet.
    """
    visible_course_certs = _filter_visible_course_certificates(qs.filter(course_credentials__isnull=False))
    visible_program_certs = _filter_visible_program_certificates(qs.filter(program_credentials__isnull=False))
    visible_certs = visible_course_certs | visible_program_certs

    return visible_certs


def _filter_visible_course_certificates(query_set: "QuerySet") -> "QuerySet":
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


def _filter_visible_program_certificates(query_set: "QuerySet") -> "QuerySet":
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
    visible_program_cert_ids = []  # type: list[Optional[int]]
    for user_credential in query_set:
        program_visible_date = _get_program_certificate_visible_date(user_credential)
        if program_visible_date and program_visible_date <= now:
            visible_program_cert_ids.append(user_credential.id)
    return UserCredential.objects.filter(pk__in=visible_program_cert_ids)


def _get_program_certificate_visible_date(user_program_credential: UserCredential) -> Optional[datetime.datetime]:
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
    last_date = None  # type: Optional[datetime.datetime]
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


def _get_issue_date_for_course_credential(course_run_user_credentials: UserCredential) -> "DateTimeField":
    """
    Retrieves the issue date for a given course run UserCredential. This method
    attempts to find the date based on the certificate availability date
    and falls back to created date.

    Arguments:
        course_run_user_credentials (UserCredential): A Course Run UserCredential

    Returns:
        datetime: The datetime that the credential should be visible and was issued.
    """
    if course_run_user_credentials.credential.certificate_available_date:
        return course_run_user_credentials.credential.certificate_available_date
    return course_run_user_credentials.created


def get_credential_visible_dates(
    user_credentials, use_date_override: bool = False
) -> Dict[UserCredential, "DateTimeField"]:
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
        elif user_credential.program_credentials.exists():
            date = _get_program_certificate_visible_date(user_credential)

        visible_date_dict[user_credential] = date

    return visible_date_dict


def get_credential_visible_date(
    user_credential: UserCredential, use_date_override: bool = False
) -> Dict[UserCredential, "DateTimeField"]:
    """Simpler, one-credential version of get_credential_visible_dates."""
    return get_credential_visible_dates([user_credential], use_date_override)[user_credential]


def send_program_certificate_created_message(
    username: str, program_certificate: "ProgramCertificate", lms_user_id: int
) -> None:
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
