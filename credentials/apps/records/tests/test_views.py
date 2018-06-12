"""
Tests for records rendering views.
"""
import uuid

from django.template.loader import select_template
from django.test import TestCase
from django.urls import reverse
from mock import patch
from waffle.testutils import override_flag

from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory, UserCredentialFactory
from ..constants import WAFFLE_FLAG_RECORDS


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
class RecordsViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=user.username, password=USER_PASSWORD)

    def _render_records(self, program_data=None, status_code=200):
        """ Helper method to render a user certificate."""
        if program_data is None:
            program_data = []

        with patch('credentials.apps.records.views.RecordsView._get_programs') as get_programs:
            get_programs.return_value = program_data
            response = self.client.get(reverse('records:index'))
            self.assertEqual(response.status_code, status_code)

        return response

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    def test_no_anonymous_access(self):
        """ Verify that the view rejects non-logged-in users. """
        self.client.logout()
        response = self._render_records(status_code=302)
        self.assertRegex(response.url, '^/login/.*')  # pylint: disable=deprecated-method

    @override_flag(WAFFLE_FLAG_RECORDS, active=False)
    def test_feature_toggle(self):
        """ Verify that the view rejects everyone without the waffle flag. """
        self._render_records(status_code=404)

    def test_normal_access(self):
        """ Verify that the view works in default case. """
        response = self._render_records()
        response_context_data = response.context_data

        self.assertContains(response, 'My Records')

        actual_child_templates = response_context_data['child_templates']
        self.assert_matching_template_origin(actual_child_templates['footer'], '_footer.html')
        self.assert_matching_template_origin(actual_child_templates['header'], '_header.html')

    def test_xss(self):
        """ Verify that the view protects against xss in translations. """
        response = self._render_records([
            {
                "name": "<xss>",
                'partner': 'XSS',
                'uuid': 'uuid',
            },
        ])

        # Test that the data is parsed from an escaped string
        self.assertContains(response, 'JSON.parse(\'[{' +
                                      '\\u0022name\\u0022: \\u0022\\u003Cxss\\u003E\\u0022, ' +
                                      '\\u0022partner\\u0022: \\u0022XSS\\u0022, ' +
                                      '\\u0022uuid\\u0022: \\u0022uuid\\u0022' +
                                      '}]\')')
        self.assertNotContains(response, '<xss>')

    def test_help_url(self):
        """ Verify that the records help url gets loaded into the context """
        response = self._render_records()
        response_context_data = response.context_data
        self.assertIn('records_help_url', response_context_data)
        self.assertNotEqual(response_context_data['records_help_url'], '')


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
class ProgramRecordViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=user.username, password=USER_PASSWORD)

    def _render_program_record(self, record_data=None, status_code=200):
        """ Helper method to render a user certificate."""
        if record_data is None:
            record_data = {}

        with patch('credentials.apps.records.views.ProgramRecordView._get_record') as get_record:
            get_record.return_value = record_data
            response = self.client.get(reverse('records:programs', kwargs={'uuid': uuid.uuid4().hex}))
            self.assertEqual(response.status_code, status_code)

        return response

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    def test_no_anonymous_access(self):
        """ Verify that the view rejects non-logged-in users. """
        self.client.logout()
        response = self._render_program_record(status_code=302)
        self.assertRegex(response.url, '^/login/.*')  # pylint: disable=deprecated-method

    @override_flag(WAFFLE_FLAG_RECORDS, active=False)
    def test_feature_toggle(self):
        """ Verify that the view rejects everyone without the waffle flag. """
        self._render_program_record(status_code=404)

    def test_normal_access(self):
        """ Verify that the view works in default case. """
        response = self._render_program_record()
        response_context_data = response.context_data

        self.assertContains(response, 'Record')

        actual_child_templates = response_context_data['child_templates']
        self.assert_matching_template_origin(actual_child_templates['footer'], '_footer.html')
        self.assert_matching_template_origin(actual_child_templates['header'], '_header.html')

    def test_xss(self):
        """ Verify that the view protects against xss in translations. """
        response = self._render_program_record({
            "name": "<xss>",
            'program': {
                'name': '<xss>',
                'school': 'XSS School',
            },
            'uuid': 'uuid',
        })

        # Test that the data is parsed from an escaped string
        self.assertContains(response, "JSON.parse(\'{\\u0022name\\u0022: \\u0022\\u003Cxss\\u003E\\u0022, " +
                                      "\\u0022program\\u0022: {\\u0022name\\u0022: \\u0022\\u003Cxss\\u003E\\u0022, " +
                                      "\\u0022school\\u0022: \\u0022XSS School\\u0022}, \\u0022uuid\\u0022: " +
                                      "\\u0022uuid\\u0022}\')")
        self.assertNotContains(response, '<xss>')


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
class ProgramRecordTests(TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()
        user = UserFactory(username=self.USERNAME)
        self.client.login(username=user.username, password=USER_PASSWORD)
        self.user_credential = UserCredentialFactory(username=self.USERNAME)
        self.pc = ProgramCertificateFactory()
        self.user_credential.credential = self.pc
        self.user_credential.save()

    def test_user_creation(self):
        """Verify successful creation of a ProgramCertRecord and return of a uuid"""
        rev = reverse('records:cert_creation')
        data = {'username': self.USERNAME, 'program_cert_uuid': self.pc.program_uuid}
        response = self.client.post(rev, data)
        json_data = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertRegex(json_data['uuid'], UUID_PATTERN)  # pylint: disable=deprecated-method

    def test_different_user_creation(self):
        """ Verify that the view rejects a User attempting to create a ProgramCertRecord for another """
        diff_username = 'diff-user'
        rev = reverse('records:cert_creation')
        UserFactory(username=diff_username)
        data = {'username': diff_username, 'program_cert_uuid': self.pc.program_uuid}
        response = self.client.post(rev, data)

        self.assertEqual(response.status_code, 403)

    def test_no_user_credenital(self):
        """ Verify that the view rejects a User attempting to create a ProgramCertRecord for which they don't
        have the User Credentials """
        pc2 = ProgramCertificateFactory()
        rev = reverse('records:cert_creation')
        data = {'username': self.USERNAME, 'program_cert_uuid': pc2.program_uuid}
        response = self.client.post(rev, data)

        self.assertEqual(response.status_code, 404)

    def test_pcr_already_exists(self):
        """ Verify that the view returns the existing ProgramCertRecord when one already exists for the given username
        and program certificate uuid"""

        rev = reverse('records:cert_creation')
        data = {'username': self.USERNAME, 'program_cert_uuid': self.pc.program_uuid}
        response = self.client.post(rev, data)
        pcr_uuid = response.json()['uuid']
        self.assertEqual(response.status_code, 201)

        response = self.client.post(rev, data)
        pcr_uuid2 = response.json()['uuid']
        self.assertEqual(response.status_code, 200)

        self.assertEqual(pcr_uuid, pcr_uuid2)

    @override_flag(WAFFLE_FLAG_RECORDS, active=False)
    def test_feature_toggle(self):
        """ Verify that the view rejects everyone without the waffle flag. """
        rev = reverse('records:cert_creation')
        data = {'username': self.USERNAME, 'program_cert_uuid': self.pc.program_uuid}
        response = self.client.post(rev, data)

        self.assertEqual(404, response.status_code)
