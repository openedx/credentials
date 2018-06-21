"""
Tests for records rendering views.
"""
import json
import uuid

from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.template.loader import select_template
from django.test import TestCase
from django.urls import reverse
from mock import patch
from waffle.testutils import override_flag

from credentials.apps.catalog.tests.factories import (CourseFactory, CourseRunFactory, OrganizationFactory,
                                                      ProgramFactory)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.tests.factories import (CourseCertificateFactory, ProgramCertificateFactory,
                                                          UserCredentialFactory)
from credentials.apps.records.tests.factories import UserGradeFactory

from ..constants import WAFFLE_FLAG_RECORDS


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
class RecordsViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ['TestOrg1', 'TestOrg2']]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = [CourseRunFactory.create(course=self.course) for _ in range(2)]
        self.program = ProgramFactory(course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site)
        self.course_certs = [CourseCertificateFactory.create(
            course_id=course_run.key, site=self.site,
        ) for course_run in self.course_runs]
        self.program_cert = ProgramCertificateFactory.create(program_uuid=self.program.uuid, site=self.site)
        self.course_credential_content_type = ContentType.objects.get(
            app_label='credentials',
            model='coursecertificate'
        )
        self.program_credential_content_type = ContentType.objects.get(
            app_label='credentials',
            model='programcertificate'
        )
        self.course_user_credentials = [UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.course_credential_content_type,
            credential=course_cert
        ) for course_cert in self.course_certs]
        self.program_user_credentials = UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=self.program_cert
        )

        self.client.login(username=self.user.username, password=USER_PASSWORD)

    def _render_records(self, program_data=None, status_code=200):
        """ Helper method to mock and render a user certificate."""
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

    def test_completed_render_from_db(self):
        """ Verify that a program cert that is completed is the only entry, despite having course certificates """
        response = self.client.get(reverse('records:index'))
        self.assertEqual(response.status_code, 200)
        program_data = json.loads(response.context_data['programs'])
        expected_program_data = [
            {
                'name': self.program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': self.program.uuid.hex,
                'type': slugify(self.program.type),
                'progress': 'Completed',
            }
        ]
        self.assertEqual(program_data, expected_program_data)

    def test_in_progress_from_db(self):
        """ Verify that no program cert, but course certs reuslts in an In Progress program """
        # Delete the program
        self.program_cert.delete()
        response = self.client.get(reverse('records:index'))
        self.assertEqual(response.status_code, 200)
        program_data = json.loads(response.context_data['programs'])
        expected_program_data = [
            {
                'name': self.program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': self.program.uuid.hex,
                'type': slugify(self.program.type),
                'progress': 'In Progress',
            }
        ]
        self.assertEqual(program_data, expected_program_data)

    def test_multiple_programs(self):
        """ Test that multiple programs can appear, in progress and completed """
        # Create a second program, and delete the first one's certificate
        new_course = CourseFactory.create(site=self.site)
        new_course_run = CourseRunFactory.create(course=new_course)
        new_program = ProgramFactory.create(course_runs=[new_course_run], authoring_organizations=self.orgs,
                                            site=self.site)
        new_course_cert = CourseCertificateFactory.create(course_id=new_course_run.key, site=self.site)
        new_program_cert = ProgramCertificateFactory.create(program_uuid=new_program.uuid, site=self.site)
        # Make a new user credential
        UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=new_course_cert
        )
        # Make a new program credential
        UserCredentialFactory.create(
            username=self.user.username,
            credential_content_type=self.program_credential_content_type,
            credential=new_program_cert
        )
        self.program_user_credentials.delete()

        response = self.client.get(reverse('records:index'))
        self.assertEqual(response.status_code, 200)
        program_data = json.loads(response.context_data['programs'])
        expected_program_data = [
            {
                'name': self.program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': self.program.uuid.hex,
                'type': slugify(self.program.type),
                'progress': 'In Progress',
            },
            {
                'name': new_program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': new_program.uuid.hex,
                'type': slugify(new_program.type),
                'progress': 'Completed',
            }
        ]
        self.assertEqual(program_data, expected_program_data)


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
class ProgramRecordViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()

        self.user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=self.user.username, password=USER_PASSWORD)

        self.course = CourseFactory(site=self.site)
        self.course_runs = [CourseRunFactory(course=self.course) for _ in range(2)]

        self.user_grade_low = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                               course_run=self.course_runs[0], letter_grade='C', percent_grade=0.70)
        self.user_grade_high = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                                course_run=self.course_runs[1], letter_grade='A', percent_grade=1.00)

        self.course_certs = [CourseCertificateFactory(course_id=course_run.key, site=self.site)
                             for course_run in self.course_runs]
        credential_content_type = ContentType.objects.get(app_label='credentials', model='coursecertificate')
        self.user_credentials = [UserCredentialFactory(username=self.MOCK_USER_DATA['username'],
                                 credential_content_type=credential_content_type, credential=course_cert)
                                 for course_cert in self.course_certs]
        self.org_names = ['CCC', 'AAA', 'BBB']
        self.orgs = [OrganizationFactory(name=name, site=self.site) for name in self.org_names]
        self.program = ProgramFactory(course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site)

    def _render_program_record(self, record_data=None, status_code=200):
        """ Helper method to mock rendering a user certificate."""
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

    def test_highest_grades(self):
        """ Verify that the view only shows the highest grades and counts attemps """
        response = self.client.get(reverse('records:programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 1)
        grade = grades[0]

        expected_grade = {'name': self.course.title,
                          'school': '',
                          'attempts': 2,
                          'course_id': self.course.key,
                          'issue_date': self.course_certs[1].modified.isoformat(),
                          'percent_grade': 1.0,
                          'letter_grade': 'A'}

        self.assertEqual(grade, expected_grade)

    def test_organization_order(self):
        """ Test that the organizations are returned in the order they were added """
        self.course.owners = self.orgs
        response = self.client.get(reverse('records:programs', kwargs={'uuid': self.program.uuid.hex}))
        program_data = json.loads(response.context_data['record'])['program']
        grade = json.loads(response.context_data['record'])['grades'][0]

        self.assertEqual(program_data['school'], ', '.join(self.org_names))
        self.assertEqual(grade['school'], ', '.join(self.org_names))

    def test_learner_data(self):
        """ Test that the learner data is returned succesfully """
        response = self.client.get(reverse('records:programs', kwargs={'uuid': self.program.uuid.hex}))
        learner_data = json.loads(response.context_data['record'])['learner']

        expected = {'full_name': self.user.get_full_name(),
                    'username': str(self.user),
                    'email': self.user.email}

        self.assertEqual(learner_data, expected)

    def test_program_data(self):
        """ Test that the program data is returned successfully """
        response = self.client.get(reverse('records:programs', kwargs={'uuid': self.program.uuid.hex}))
        program_data = json.loads(response.context_data['record'])['program']

        expected = {'name': self.program.title,
                    'type': slugify(self.program.type),
                    'school': ', '.join(self.org_names)}

        self.assertEqual(program_data, expected)

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

    def test_no_user_credential(self):
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
