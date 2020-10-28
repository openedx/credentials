import logging
import urllib

from django.conf import settings
from django.urls import reverse
from edx_ace import Recipient, ace

from credentials.apps.catalog.models import Program
from credentials.apps.core.models import User
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.messages import ProgramCreditRequest
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway


logger = logging.getLogger(__name__)


def send_updated_emails_for_program(request, username, program_certificate):
    """ If the user has previously sent an email to a pathway org, we want to send
    an updated one when they finish the program.  This function is called from the
    credentials Program Certificate awarding API """
    site = program_certificate.site
    user = User.objects.get(username=username)
    program_uuid = program_certificate.program_uuid

    program = Program.objects.prefetch_related('pathways').get(site=site, uuid=program_uuid)
    pathways_set = frozenset(program.pathways.all())

    user_pathways = UserCreditPathway.objects.select_related('pathway').filter(
        user=user, pathway__in=pathways_set, status=UserCreditPathwayStatus.SENT)

    # Return here if the user doesn't have a program cert record
    try:
        pcr = ProgramCertRecord.objects.get(program=program, user=user)
    except ProgramCertRecord.DoesNotExist:
        logger.exception("Program Cert Record for user_uuid %s, program_uuid %s does not exist",
                         user.id,
                         program.uuid)
        return

    # Send emails for those already marked as "SENT"
    for user_pathway in user_pathways:

        pathway = user_pathway.pathway
        record_path = reverse('records:public_programs', kwargs={'uuid': pcr.uuid.hex})
        record_link = request.build_absolute_uri(record_path)
        csv_link = urllib.parse.urljoin(record_link, "csv")

        msg = ProgramCreditRequest(site, user.email).personalize(
            recipient=Recipient(username=None, email_address=pathway.email),
            language=program_certificate.language,
            user_context={
                'pathway_name': pathway.name,
                'program_name': program.title,
                'record_link': record_link,
                'user_full_name': user.get_full_name(),
                'program_completed': True,
                'previously_sent': True,
                'csv_link': csv_link,
            },
        )
        ace.send(msg)


def masquerading_authorized(masquerader, target):
    """
    Checks whether a user has the permissions to masquerade as the target user.

    Overrides django-hijack's default authorization function to prevent
    superusers from masquerading as other superusers.

    By default only superusers are allowed to masquerade, unless
    HIJACK_AUTHORIZE_STAFF is enabled in settings.

    By default, staff are not able to masquerade as staff unless
    HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF is enabled in settings.

    Adapted from:
    https://github.com/arteria/django-hijack/blob/4dd897761952adf387fb71822e3e76bc3d0deb51/hijack/helpers.py#L77
    """
    if target.is_superuser:
        return False

    if masquerader.is_superuser:
        return True

    if masquerader.is_staff and getattr(settings, 'HIJACK_AUTHORIZE_STAFF', False):
        if target.is_staff and not getattr(settings, 'HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF', False):
            return False

        return True

    return False
