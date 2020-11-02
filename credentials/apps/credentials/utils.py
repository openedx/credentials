import datetime
import logging
import textwrap
from itertools import groupby

from django.conf import settings
from django.db.models import Q
from edx_ace import Recipient, ace

from credentials.apps.catalog.models import Program
from credentials.apps.core.models import User
from credentials.apps.credentials.messages import ProgramCertificateIssuedMessage
from credentials.apps.credentials.models import UserCredentialAttribute


log = logging.getLogger(__name__)

VISIBLE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def to_language(locale):
    if locale is None:
        return None
    # Convert to bytes to get ascii-lowercasing, to avoid the Turkish I problem.
    return locale.replace('_', '-').encode().lower().decode()


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
        attributes (list): List of dicts contains attributes data

    Returns:
        Boolean: Return True only if data has no duplicated namespace and name

    """

    def keyfunc(attribute):
        return attribute['name']

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True


def datetime_from_visible_date(date):
    """ Turn a string version of a datetime, provided to us by the LMS in a particular format it uses for
        visible_date attributes, and turn it into a datetime object. """
    try:
        parsed = datetime.datetime.strptime(date, VISIBLE_DATE_FORMAT)
        # The timezone is always UTC (as indicated by the Z). It looks like in python3.7, we could
        # just use %z instead of replacing the tzinfo with a UTC value.
        return parsed.replace(tzinfo=datetime.timezone.utc)
    except ValueError as e:
        log.exception('%s', e)
        return None


def filter_visible(qs):
    """ Filters a UserCredentials queryset by excluding credentials that aren't supposed to be visible yet. """
    # The visible_date attribute holds a string value, not a datetime one. But we can compare as a string
    # because the format is so strict - it will still lexically compare as less/greater-than.
    nowstr = datetime.datetime.now(datetime.timezone.utc).strftime(VISIBLE_DATE_FORMAT)
    return qs.filter(
        Q(attributes__name='visible_date', attributes__value__lte=nowstr) | ~Q(attributes__name='visible_date')
    )


def get_credential_visible_dates(user_credentials):
    """
    Calculates visible date for a collection of UserCredentials.
    Returns a dictionary of {UserCredential: datetime}.
    Guaranteed to return a datetime object for each credential.
    """

    visible_dates = UserCredentialAttribute.objects.prefetch_related('user_credential__credential').filter(
        user_credential__in=user_credentials, name='visible_date')

    visible_date_dict = {
        visible_date.user_credential: datetime_from_visible_date(visible_date.value)
        for visible_date in visible_dates
    }

    for user_credential in user_credentials:
        current = visible_date_dict.get(user_credential)
        if current is None:
            visible_date_dict[user_credential] = user_credential.created

    return visible_date_dict


def get_credential_visible_date(user_credential):
    """ Simpler, one-credential version of get_credential_visible_dates. """
    return get_credential_visible_dates([user_credential])[user_credential]


def send_program_certificate_created_message(username, program_certificate):
    """
    If the learner has earned a Program Certificate then we go ahead and send them an automated email congratulating
    them for their achievement. Emails to learners in credit eligible Programs will contain additional information.
    """
    user = User.objects.get(username=username)
    program_uuid = program_certificate.program_uuid
    program = Program.objects.get(site=program_certificate.site, uuid=program_uuid)

    custom_completion_email_settings = getattr(settings, 'CUSTOM_COMPLETION_EMAIL_TEMPLATE_EXTRA', {})
    custom_completion_email_content = (
        custom_completion_email_settings.get(str(program_uuid), {})
        or custom_completion_email_settings.get(program.type_slug, {})
        or {}
    )
    try:
        msg = ProgramCertificateIssuedMessage(program_certificate.site, user.email).personalize(
            recipient=Recipient(username=user.username, email_address=user.email),
            language=program_certificate.language,
            user_context={
                'program_title': program.title,
                'program_type': program.type,
                'custom_email_html_template_extra': custom_completion_email_content.get('html', ''),
                # remove any leading spaces of the plaintext content so that the email doesn't look horrendous
                'custom_email_plaintext_template_extra': textwrap.dedent(
                    custom_completion_email_content.get('plaintext', '')
                ),
            },
        )
        log.info("Sending Program completion email to learner with id [{}] in Program [{}]".format(
            user.id, program_uuid)
        )
        ace.send(msg)
    # We wouldn't want any issues that arise from formatting or sending this email message to interrupt the process
    # of issuing a learner their Program Certificate. We cast a wide net for exceptions here for this reason.
    except Exception as ex:  # pylint: disable=broad-except
        log.exception("Unable to send email to learner with id: [{}] for Program [{}]. Error occurred while "
                      "attempting to format or send message: {}".format(user.id, program_uuid, ex))
