import urllib

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory

from credentials.apps.catalog.tests.factories import PathwayFactory, ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.tests.factories import ProgramCertRecordFactory, UserCreditPathwayFactory
from credentials.apps.records.tests.utils import dump_random_state
from credentials.apps.records.utils import masquerading_authorized, send_updated_emails_for_program


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
        self.pathway = PathwayFactory(site=self.site, programs=[self.program])
        self.pc = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)
        self.pcr = ProgramCertRecordFactory(program=self.program, user=self.user)
        self.data = {'username': self.USERNAME, 'pathway_id': self.pathway.id}
        self.url = reverse('records:share_program', kwargs={'uuid': self.program.uuid.hex})
        self.request = APIRequestFactory().get('/')

        mail.outbox = []

    def test_send_updated_email_when_program_finished(self):
        """
        Test that an additional updated email will be sent
        """
        # Mock sending an email to the partner
        UserCreditPathwayFactory(
            user=self.user,
            pathway=self.pathway,
            status=UserCreditPathwayStatus.SENT)
        self.assertEqual(0, len(mail.outbox))

        send_updated_emails_for_program(self.request, self.USERNAME, self.pc)

        # Check that another email was sent
        self.assertEqual(1, len(mail.outbox))
        email = mail.outbox[0]
        record_path = reverse('records:public_programs', kwargs={'uuid': self.pcr.uuid.hex})
        expected_record_link = self.request.build_absolute_uri(record_path)
        expected_csv_link = urllib.parse.urljoin(expected_record_link, "csv")
        self.assertIn(self.program.title + ' Updated Credit Request for', email.subject)
        self.assertIn(expected_record_link, email.body)
        self.assertIn(expected_csv_link, email.body)

    def test_no_previous_email_sent(self):
        """
        Test that no additional email is sent if the user hasn't previously sent one
        """
        self.assertEqual(0, len(mail.outbox))

        send_updated_emails_for_program(self.request, self.USERNAME, self.pc)

        # Check that no email was sent
        self.assertEqual(0, len(mail.outbox))


class MasqueradingAuthorizedTests(TestCase):
    """ Tests for masquerading authorization. """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.staff_user = UserFactory(is_staff=True)
        self.superuser = UserFactory(is_superuser=True)

    def test_default_authorization(self):
        """
        Tests that the correct authorization is given with the default settings.

        For default settings, HIJACK_AUTHORIZE_STAFF = True,
        HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF = False.
        """
        self.assertEqual(masquerading_authorized(self.user, self.user), False)
        self.assertEqual(masquerading_authorized(self.user, self.staff_user), False)
        self.assertEqual(masquerading_authorized(self.user, self.superuser), False)
        self.assertEqual(masquerading_authorized(self.staff_user, self.user), True)
        self.assertEqual(masquerading_authorized(self.staff_user, self.staff_user), False)
        self.assertEqual(masquerading_authorized(self.staff_user, self.superuser), False)
        self.assertEqual(masquerading_authorized(self.superuser, self.user), True)
        self.assertEqual(masquerading_authorized(self.superuser, self.staff_user), True)
        self.assertEqual(masquerading_authorized(self.superuser, self.superuser), False)

    @override_settings(HIJACK_AUTHORIZE_STAFF=False, HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF=False)
    def test_no_staff_authorization(self):
        """ Tests correct authorization when staff can not masquerade. """
        self.assertEqual(masquerading_authorized(self.user, self.user), False)
        self.assertEqual(masquerading_authorized(self.user, self.staff_user), False)
        self.assertEqual(masquerading_authorized(self.user, self.superuser), False)
        self.assertEqual(masquerading_authorized(self.staff_user, self.user), False)
        self.assertEqual(masquerading_authorized(self.staff_user, self.staff_user), False)
        self.assertEqual(masquerading_authorized(self.staff_user, self.superuser), False)
        self.assertEqual(masquerading_authorized(self.superuser, self.user), True)
        self.assertEqual(masquerading_authorized(self.superuser, self.staff_user), True)
        self.assertEqual(masquerading_authorized(self.superuser, self.superuser), False)

    @override_settings(HIJACK_AUTHORIZE_STAFF=True, HIJACK_AUTHORIZE_STAFF_TO_HIJACK_STAFF=True)
    def test_full_staff_authorization(self):
        """ Tests correct authorization when staff can masquerade as staff. """
        self.assertEqual(masquerading_authorized(self.user, self.user), False)
        self.assertEqual(masquerading_authorized(self.user, self.staff_user), False)
        self.assertEqual(masquerading_authorized(self.user, self.superuser), False)
        self.assertEqual(masquerading_authorized(self.staff_user, self.user), True)
        self.assertEqual(masquerading_authorized(self.staff_user, self.staff_user), True)
        self.assertEqual(masquerading_authorized(self.staff_user, self.superuser), False)
        self.assertEqual(masquerading_authorized(self.superuser, self.user), True)
        self.assertEqual(masquerading_authorized(self.superuser, self.staff_user), True)
        self.assertEqual(masquerading_authorized(self.superuser, self.superuser), False)
