from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from credentials.apps.catalog.tests.factories import CreditPathwayFactory, ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.tests.factories import ProgramCertRecordFactory, UserCreditPathwayFactory
from credentials.apps.records.tests.utils import dump_random_state
from credentials.apps.records.utils import send_updated_emails_for_program


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class UpdatedProgramEmailTests(SiteMixin, TestCase):
    """ Tests for sending an update """
    USERNAME = 'test-records-user'

    def setUp(self):
        super().setUp()
        dump_random_state()
        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)
        self.pathway = CreditPathwayFactory(site=self.site, programs=[self.program])
        self.pc = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)
        self.pcr = ProgramCertRecordFactory(program=self.program, user=self.user)
        self.data = {'username': self.USERNAME, 'pathway_id': self.pathway.id}
        self.url = reverse('records:share_program', kwargs={'uuid': self.program.uuid.hex})

        mail.outbox = []

    def test_send_updated_email_when_program_finished(self):
        """
        Test that an additional updated email will be sent
        """
        # Mock sending an email to the partner
        UserCreditPathwayFactory(
            user=self.user,
            credit_pathway=self.pathway,
            status=UserCreditPathwayStatus.SENT)
        self.assertEqual(0, len(mail.outbox))

        send_updated_emails_for_program(self.USERNAME, self.pc)

        # Check that another email was sent
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        self.assertIn(self.program.title + ' Updated Credit Request for', email.subject)

    def test_no_previous_email_sent(self):
        """
        Test that no additional email is sent if the user hasn't previously sent one
        """
        self.assertEqual(0, len(mail.outbox))

        send_updated_emails_for_program(self.USERNAME, self.pc)

        # Check that no email was sent
        self.assertEqual(0, len(mail.outbox))
