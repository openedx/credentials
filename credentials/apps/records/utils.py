import logging
import urllib

from django.urls import reverse
from edx_ace import Recipient, ace

from credentials.apps.catalog.models import Program
from credentials.apps.core.models import User
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.messages import ProgramCreditRequest
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway

logger = logging.getLogger(__name__)


def send_updated_emails_for_program(username, program_certificate):
        """ If the user has previously sent an email to a pathway org, we want to send
        an updated one when they finish the program.  This function is called from the
        credentials Program Certificate awarding API """
        site = program_certificate.site
        user = User.objects.get(username=username)
        program_uuid = program_certificate.program_uuid

        program = Program.objects.prefetch_related('pathways').get(site=site, uuid=program_uuid)
        pathways_set = frozenset(program.pathways.all())

        user_pathways = UserCreditPathway.objects.select_related('credit_pathway').filter(
            user=user, credit_pathway__in=pathways_set, status=UserCreditPathwayStatus.SENT)

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

            pathway = user_pathway.credit_pathway
            record_path = reverse('records:public_programs', kwargs={'uuid': pcr.uuid.hex})
            record_link = site.domain + record_path
            csv_link = urllib.parse.urljoin(record_link, "csv")

            msg = ProgramCreditRequest(site).personalize(
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
