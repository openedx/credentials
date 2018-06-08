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
