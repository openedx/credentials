"""
Tests for records rendering views.
"""
import csv
import datetime
import io
import json
import urllib.parse
import uuid
from unittest.mock import patch

import ddt
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.template.defaultfilters import slugify
from django.template.loader import select_template
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from credentials.apps.catalog.models import Program
from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    PathwayFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialAttributeFactory,
    UserCredentialFactory,
)
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway
from credentials.apps.records.tests.factories import (
    ProgramCertRecordFactory,
    UserCreditPathwayFactory,
    UserGradeFactory,
)
from credentials.apps.records.tests.utils import dump_random_state
from credentials.shared.constants import PathwayType


JSON_CONTENT_TYPE = 'application/json'


@ddt.ddt
class RecordsViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        dump_random_state()

        self.user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ['TestOrg1', 'TestOrg2']]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(title="TestProgram1",
                                      course_runs=self.course_runs,
                                      authoring_organizations=self.orgs,
                                      site=self.site)
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
        self.program_user_credential = UserCredentialFactory.create(
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
        self.assertRegex(response.url, '^/login/.*')

    def test_normal_access(self):
        """ Verify that the view works in default case. """
        response = self._render_records()
        response_context_data = response.context_data

        self.assertContains(response, 'My Learner Records')

        actual_child_templates = response_context_data['child_templates']
        self.assert_matching_template_origin(actual_child_templates['footer'], '_footer.html')
        self.assert_matching_template_origin(actual_child_templates['header'], '_header.html')
        self.assert_matching_template_origin(actual_child_templates['masquerade'], '_masquerade.html')

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
        self.assertContains(response, 'JSON.parse(\'[{'
                            + '\\u0022name\\u0022: \\u0022\\u003Cxss\\u003E\\u0022, '
                            + '\\u0022partner\\u0022: \\u0022XSS\\u0022, '
                            + '\\u0022uuid\\u0022: \\u0022uuid\\u0022'
                            + '}]\')')
        self.assertNotContains(response, '<xss>')

    def test_help_url(self):
        """ Verify that the records help url gets loaded into the context """
        response = self._render_records()
        response_context_data = response.context_data
        self.assertIn('records_help_url', response_context_data)
        self.assertNotEqual(response_context_data['records_help_url'], '')

    @ddt.data(
        (Program.ACTIVE, True),
        (Program.RETIRED, True),
        (Program.DELETED, False),
        (Program.UNPUBLISHED, False),
    )
    @ddt.unpack
    def test_completed_render_from_db(self, status, visible):
        """ Verify that a program cert that is completed is returned correctly, with different statuses """
        self.program.status = status
        self.program.save()

        response = self.client.get(reverse('records:index'))
        self.assertEqual(response.status_code, 200)
        program_data = json.loads(response.context_data['programs'])

        expected_program_data = [
            {
                'name': self.program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': self.program.uuid.hex,
                'type': slugify(self.program.type),
                'completed': True,
                'empty': False,
            }
        ]
        self.assertEqual(program_data, expected_program_data if visible else [])

    def test_in_progress_from_db(self):
        """ Verify that no program cert, but course certs results in an In Progress program """
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
                'completed': False,
                'empty': False,
            }
        ]
        self.assertEqual(program_data, expected_program_data)

    def test_not_visible_from_db(self):
        """ Test that the program's visible_date is considered """
        UserCredentialAttributeFactory(
            user_credential=self.program_user_credential,
            name='visible_date',
            value='9999-01-01T01:01:01Z',
        )
        response = self.client.get(reverse('records:index'))
        self.assertFalse(json.loads(response.context_data['programs'])[0]['completed'])

    def test_multiple_programs(self):
        """ Test that multiple programs can appear, in progress and completed """
        # Create a second program, and delete the first one's certificate
        new_course = CourseFactory.create(site=self.site)
        new_course_run = CourseRunFactory.create(course=new_course)

        new_program = ProgramFactory.create(title='ZTestProgram',
                                            course_runs=[new_course_run],
                                            authoring_organizations=self.orgs,
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
        self.program_user_credential.delete()

        response = self.client.get(reverse('records:index'))
        self.assertEqual(response.status_code, 200)
        program_data = json.loads(response.context_data['programs'])
        expected_program_data = [
            {
                'name': self.program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': self.program.uuid.hex,
                'type': slugify(self.program.type),
                'completed': False,
                'empty': False,
            },
            {
                'name': new_program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': new_program.uuid.hex,
                'type': slugify(new_program.type),
                'completed': True,
                'empty': False,
            }
        ]
        self.assertEqual(program_data, expected_program_data)


# This view shares almost all the code with RecordsView above. So we'll just test the interesting differences.
@ddt.ddt
class ProgramListingViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        dump_random_state()

        self.user = UserFactory(username=self.MOCK_USER_DATA['username'], is_staff=True)
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ['TestOrg1', 'TestOrg2']]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(title="TestProgram1",
                                      course_runs=self.course_runs,
                                      authoring_organizations=self.orgs,
                                      site=self.site)
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

    def _render_listing(self, expected_program_data=None, status_code=200):
        """ Helper method to mock and render a user certificate."""
        response = self.client.get(reverse('program_listing'))
        self.assertEqual(response.status_code, status_code)

        if expected_program_data is not None:
            program_data = json.loads(response.context_data['programs'])
            self.assertListEqual(program_data, expected_program_data)

        return response

    def _default_program_data(self, overrides=None):
        # if nothing is adjusted, this is the expected listing
        data = [
            {
                'name': self.program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': self.program.uuid.hex,
                'type': slugify(self.program.type),
                'completed': True,
                'empty': False,
            },
        ]

        if overrides is not None:
            data[0].update(overrides)

        return data

    def _verify_normal_access(self):
        response = self._render_listing()
        response_context_data = response.context_data

        self.assertContains(response, 'Program Listing View')

        actual_child_templates = response_context_data['child_templates']
        self.assert_matching_template_origin(actual_child_templates['footer'], '_footer.html')
        self.assert_matching_template_origin(actual_child_templates['header'], '_header.html')
        self.assertNotIn('masquerade', actual_child_templates)  # no masquerading on this view

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    def test_no_anonymous_access(self):
        """ Verify that the view rejects non-logged-in users. """
        self.client.logout()
        response = self._render_listing(status_code=302)
        self.assertRegex(response.url, '^/login/.*')

    def test_non_superuser_access(self):
        """ Verify that the view rejects non-superuser users. """
        self.user.is_superuser = False
        self.user.is_staff = False
        self.user.save()
        self._render_listing(status_code=404)

    def test_only_staff_access(self):
        """ Verify that the view rejects non-staff users. """
        self.user.is_staff = False
        self.user.save()
        self._render_listing(status_code=404)

    def test_normal_access_superuser(self):
        """ Verify that the view works with only superuser, no staff. """
        self.user.is_superuser = True
        self.user.is_staff = False
        self._verify_normal_access()

    def test_normal_access_as_staff(self):
        """ Verify that the view works in default case. Staff is set in the setup method."""
        self._verify_normal_access()

    @ddt.data(
        (Program.ACTIVE, True),
        (Program.RETIRED, False),  # this is different from RecordsView
        (Program.DELETED, False),
        (Program.UNPUBLISHED, False),
    )
    @ddt.unpack
    def test_completed_render_from_db(self, status, visible):
        """ Verify that a program cert that is completed is returned correctly, with different statuses """
        self.program.status = status
        self.program.save()

        data = self._default_program_data() if visible else []
        self._render_listing(expected_program_data=data)

    def test_in_progress_from_db(self):
        """ Verify that no program cert, but course certs results in an In Progress program """
        # Delete the program cert
        self.program_cert.delete()

        data = self._default_program_data(overrides={'completed': False})
        self._render_listing(expected_program_data=data)

    def test_empty_programs(self):
        """ Test that a program with no certs shows as empty """
        # Delete all certs
        for cert in self.course_certs:
            cert.delete()
        self.program_cert.delete()

        data = self._default_program_data(overrides={'completed': False, 'empty': True})
        self._render_listing(expected_program_data=data)


@ddt.ddt
class ProgramRecordViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        dump_random_state()

        self.user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=self.user.username, password=USER_PASSWORD)

        self.course = CourseFactory(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(3, course=self.course)

        self.user_grade_low = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                               course_run=self.course_runs[0], letter_grade='A', percent_grade=0.70)
        self.user_grade_high = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                                course_run=self.course_runs[1], letter_grade='C', percent_grade=1.00)
        self.user_grade_revoked_cert = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                                        course_run=self.course_runs[2], letter_grade='B',
                                                        percent_grade=.80)

        self.course_certs = [CourseCertificateFactory(course_id=course_run.key, site=self.site)
                             for course_run in self.course_runs]
        self.credential_content_type = ContentType.objects.get(app_label='credentials', model='coursecertificate')
        self.program_cert = ProgramCertificateFactory(site=self.site)
        self.program_content_type = ContentType.objects.get(app_label='credentials', model='programcertificate')
        self.user_credentials = [UserCredentialFactory(username=self.MOCK_USER_DATA['username'],
                                 credential_content_type=self.credential_content_type, credential=course_cert)
                                 for course_cert in self.course_certs]
        self.user_credentials[2].status = UserCredential.REVOKED
        self.user_credentials[2].save()
        self.org_names = ['CCC', 'AAA', 'BBB']
        self.orgs = [OrganizationFactory(name=name, site=self.site) for name in self.org_names]
        self.program = ProgramFactory(course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site,
                                      uuid=self.program_cert.program_uuid)
        self.pcr = ProgramCertRecordFactory(program=self.program, user=self.user)

        self.pathway = PathwayFactory(site=self.site)
        self.pathway.programs.set([self.program])

    def _render_program_record(self, record_data=None, status_code=200):
        """ Helper method to mock rendering a user certificate."""
        if record_data is None:
            record_data = {}

        with patch('credentials.apps.records.views.ProgramRecordView._get_record') as get_record:
            get_record.return_value = record_data
            response = self.client.get(reverse('records:private_programs', kwargs={'uuid': uuid.uuid4().hex}))
            self.assertEqual(response.status_code, status_code)

        return response

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    def test_no_anonymous_access_private(self):
        """ Verify that the private view rejects non-logged-in users. """
        self.client.logout()
        response = self._render_program_record(status_code=302)
        self.assertRegex(response.url, '^/login/.*')

    def test_anonymous_access_public(self):
        """ Verify that the public view does not reject non-logged-in users"""
        self.client.logout()
        response = self.client.get(reverse('records:public_programs', kwargs={'uuid': self.pcr.uuid.hex}))
        self.assertContains(response, 'Record')

    @ddt.data(True, False)
    def test_access_to_empty_record(self, is_superuser):
        """ Verify that the an empty record rejects non-superusers. """
        # Make sure no credentials exist
        self.user.is_superuser = is_superuser
        self.user.save()

        # Get rid of all credentials
        for credential in self.user_credentials:
            credential.status = UserCredential.REVOKED
            credential.save()

        expected_code = 200 if is_superuser else 404

        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        self.assertEqual(response.status_code, expected_code)

        # Confirm it is indeed reported as empty
        if is_superuser:
            program_data = json.loads(response.context_data['record'])['program']
            self.assertTrue(program_data['empty'])

    def test_normal_access(self):
        """ Verify that the view works in default case. """
        response = self._render_program_record()
        response_context_data = response.context_data

        self.assertContains(response, 'Record')

        actual_child_templates = response_context_data['child_templates']
        self.assert_matching_template_origin(actual_child_templates['footer'], '_footer.html')
        self.assert_matching_template_origin(actual_child_templates['header'], '_header.html')
        self.assert_matching_template_origin(actual_child_templates['masquerade'], '_masquerade.html')

    def test_public_access(self):
        """ Verify that the public view instructs front end to be public """
        response = self.client.get(reverse('records:public_programs', kwargs={'uuid': self.pcr.uuid.hex}))
        is_public = response.context_data['is_public']
        self.assertTrue(is_public)

    def test_private_access(self):
        """ Verify that the private view instructs front end to be private """
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        is_public = response.context_data['is_public']
        self.assertFalse(is_public)

    def test_public_private_data(self):
        """ Verify that the public and private views return the same record data """
        response = self.client.get(reverse('records:public_programs', kwargs={'uuid': self.pcr.uuid.hex}))
        public_data = json.loads(response.context_data['record'])

        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        private_data = json.loads(response.context_data['record'])

        self.assertEqual(private_data, public_data)

    def test_highest_grades(self):
        """ Verify that the view only shows the highest *percentage* grade

            Also verified that the attempts are counted correctly, even with revoked certs
        """
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 1)
        grade = grades[0]

        expected_grade = {'name': self.course_runs[1].title,
                          'school': '',
                          'attempts': 3,
                          'course_id': self.course_runs[1].key,
                          'issue_date': self.user_credentials[1].created.isoformat(),
                          'percent_grade': self.user_grade_high.percent_grade,
                          'letter_grade': self.user_grade_high.letter_grade, }

        self.assertEqual(grade, expected_grade)

    def test_visible_date_as_issue_date(self):
        """ Verify that we show visible_date when available """
        UserCredentialAttributeFactory(user_credential=self.user_credentials[1], name='visible_date',
                                       value='2017-07-31T09:32:46Z')
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 1)
        self.assertEqual(grades[0]['issue_date'], '2017-07-31T09:32:46+00:00')

    def test_future_visible_date_not_shown(self):
        """ Verify that we don't show certificates with a visible_date in the future """
        UserCredentialAttributeFactory(user_credential=self.user_credentials[1], name='visible_date',
                                       value=datetime.datetime.max.strftime('%Y-%m-%dT%H:%M:%SZ'))
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 1)
        self.assertEqual(grades[0]['course_id'], self.course_runs[0].key)  # 0 instead of 1 now that 1 is in future
        self.assertEqual(grades[0]['issue_date'], self.user_credentials[0].created.isoformat())

    @ddt.data(
        ('9999-01-01T01:01:01Z', False),
        ('1970-01-01T01:01:01Z', True),
        (None, True),
    )
    @ddt.unpack
    def test_program_visible_date(self, date, completed):
        """ Test that the program's visible_date is considered """
        program_credential = UserCredentialFactory(
            username=self.MOCK_USER_DATA['username'], credential_content_type=self.program_content_type,
            credential=self.program_cert)
        if date:
            UserCredentialAttributeFactory(
                user_credential=program_credential,
                name='visible_date',
                value=date,
            )
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        self.assertEqual(json.loads(response.context_data['record'])['program']['completed'], completed)

    def test_organization_order(self):
        """ Test that the organizations are returned in the order they were added """
        self.course.owners.set(self.orgs)
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        program_data = json.loads(response.context_data['record'])['program']
        grade = json.loads(response.context_data['record'])['grades'][0]

        self.assertEqual(program_data['school'], ', '.join(self.org_names))
        self.assertEqual(grade['school'], ', '.join(self.org_names))

    def test_course_run_order(self):
        """ Test that the course_runs are returned in the program order """
        new_course_run = CourseRunFactory()
        self.program.course_runs.add(new_course_run)
        UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                         course_run=new_course_run, letter_grade='C',
                         percent_grade=.70)
        new_course_cert = CourseCertificateFactory(course_id=new_course_run.key, site=self.site)
        UserCredentialFactory(username=self.MOCK_USER_DATA['username'],
                              credential_content_type=self.credential_content_type,
                              credential=new_course_cert)

        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']

        expected_course_run_keys = [course_run.key for course_run in [self.course_runs[1], new_course_run]]
        actual_course_run_keys = [grade['course_id'] for grade in grades]

        self.assertEqual(expected_course_run_keys, actual_course_run_keys)

    def test_course_run_no_credential(self):
        """ Adds a course run with no credential and tests that it does appear in the results """
        new_course_run = CourseRunFactory()
        self.program.course_runs.add(new_course_run)
        UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                         course_run=new_course_run, letter_grade='F',
                         percent_grade=.05)
        CourseCertificateFactory(course_id=new_course_run.key, site=self.site)

        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 2)

        self.assertEqual(new_course_run.course.title, grades[1]['name'])

    def test_multiple_attempts_no_cert(self):
        """ Adds a course with two failed course_run attempts (no cert) and verifies that
        the course only shows up once """
        # Only superusers can view an empty program (we could add a real cert too here, but this is a more direct test)
        self.user.is_superuser = True
        self.user.save()

        new_course = CourseFactory(site=self.site)
        new_course_runs = CourseRunFactory.create_batch(2, course=new_course)
        _ = [UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                              course_run=course_run,
                              letter_grade='F',
                              percent_grade=0.20) for course_run in new_course_runs]
        self.program.course_runs.set(new_course_runs)
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 1)

        self.assertEqual(new_course.title, grades[0]['name'])

    def test_learner_data(self):
        """ Test that the learner data is returned successfully """
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        learner_data = json.loads(response.context_data['record'])['learner']

        expected = {'full_name': self.user.get_full_name(),
                    'username': str(self.user),
                    'email': self.user.email}

        self.assertEqual(learner_data, expected)

    def test_program_data(self):
        """ Test that the program data is returned successfully """
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        program_data = json.loads(response.context_data['record'])['program']

        expected = {'name': self.program.title,
                    'type': slugify(self.program.type),
                    'type_name': self.program.type,
                    'completed': False,
                    'empty': False,
                    'last_updated': UserCredential.objects.last().created.isoformat(),
                    'school': ', '.join(self.org_names)}

        self.assertEqual(program_data, expected)

    def test_pathway_data(self):
        """ Test that the pathway data is returned successfully """
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        pathway_data = json.loads(response.context_data['record'])['pathways']

        expected = [{'name': self.pathway.name,
                     'id': self.pathway.id,
                     'status': '',
                     'is_active': True,
                     'pathway_type': PathwayType.CREDIT.value}]

        self.assertEqual(pathway_data, expected)

    def test_pathway_no_email(self):
        """ Test that a pathway without an email is inactive """
        self.pathway.email = ''
        self.pathway.save()
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        pathway_data = json.loads(response.context_data['record'])['pathways']

        expected = [{'name': self.pathway.name,
                     'id': self.pathway.id,
                     'status': '',
                     'is_active': False,
                     'pathway_type': PathwayType.CREDIT.value}]

        self.assertEqual(pathway_data, expected)

    def test_sent_pathway_status(self):
        """ Test that a user credit pathway pathway that has already been sent includes a pathway """
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user)

        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        pathway_data = json.loads(response.context_data['record'])['pathways']

        expected = [{'name': self.pathway.name,
                     'id': self.pathway.id,
                     'status': 'sent',
                     'is_active': True,
                     'pathway_type': PathwayType.CREDIT.value}]

        self.assertEqual(pathway_data, expected)

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
        self.assertContains(response, "JSON.parse(\'{\\u0022name\\u0022: \\u0022\\u003Cxss\\u003E\\u0022, "
                            + "\\u0022program\\u0022: {\\u0022name\\u0022: \\u0022\\u003Cxss\\u003E\\u0022, "
                            + "\\u0022school\\u0022: \\u0022XSS School\\u0022}, \\u0022uuid\\u0022: "
                            + "\\u0022uuid\\u0022}\')")
        self.assertNotContains(response, '<xss>')


class ProgramRecordTests(SiteMixin, TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()
        dump_random_state()

        user = UserFactory(username=self.USERNAME)
        self.client.login(username=user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)

    def test_login_required(self):
        """Verify no access without a login"""
        self.client.logout()
        rev = reverse('records:share_program', kwargs={'uuid': self.program.uuid.hex})
        data = {'username': self.USERNAME}
        response = self.client.post(rev, data)
        self.assertEqual(response.status_code, 302)  # redirect to a login page
        self.assertTrue(response.url.startswith('/login/?next='))

    def test_user_creation(self):
        """Verify successful creation of a ProgramCertRecord and return of a uuid"""
        rev = reverse('records:share_program', kwargs={'uuid': self.program.uuid.hex})
        data = {'username': self.USERNAME}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        json_data = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertRegex(json_data['url'], UUID_PATTERN)

    def test_different_user_creation(self):
        """ Verify that the view rejects a User attempting to create a ProgramCertRecord for another """
        diff_username = 'diff-user'
        rev = reverse('records:share_program', kwargs={'uuid': self.program.uuid.hex})
        UserFactory(username=diff_username)
        data = {'username': diff_username}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 403)

    def test_pcr_already_exists(self):
        """ Verify that the view returns the existing ProgramCertRecord when one already exists for the given username
        and program certificate uuid"""
        rev = reverse('records:share_program', kwargs={'uuid': self.program.uuid.hex})
        data = {'username': self.USERNAME}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        url1 = response.json()['url']
        self.assertEqual(response.status_code, 201)

        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        url2 = response.json()['url']
        self.assertEqual(response.status_code, 200)

        self.assertEqual(url1, url2)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProgramSendTests(SiteMixin, TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()

        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)
        self.pathway = PathwayFactory(site=self.site, programs=[self.program])
        self.pc = ProgramCertificateFactory(site=self.site, program_uuid=self.program.uuid)
        self.user_credential = UserCredentialFactory(username=self.USERNAME, credential=self.pc)
        self.data = {'username': self.USERNAME, 'pathway_id': self.pathway.id}
        self.url = reverse('records:send_program', kwargs={'uuid': self.program.uuid.hex})

        mail.outbox = []

    def post(self):
        jdata = json.dumps(self.data).encode('utf-8')
        return self.client.post(self.url, data=jdata, content_type=JSON_CONTENT_TYPE)

    def test_login_required(self):
        """Verify no access without a login"""
        self.client.logout()
        response = self.post()
        self.assertEqual(response.status_code, 302)  # redirect to a login page
        self.assertTrue(response.url.startswith('/login/?next='))

    def test_creates_cert_record(self):
        """ Verify that the view creates a ProgramCertRecord as needed. """
        with self.assertRaises(ProgramCertRecord.DoesNotExist):
            ProgramCertRecord.objects.get(user=self.user, program=self.program)

        response = self.post()
        self.assertEqual(response.status_code, 200)

        ProgramCertRecord.objects.get(user=self.user, program=self.program)

    def test_different_user(self):
        """ Verify that the view rejects a User attempting to send a program """
        diff_username = 'diff-user'
        UserFactory(username=diff_username)
        self.data['username'] = diff_username

        response = self.post()
        self.assertEqual(response.status_code, 403)

    @patch('credentials.apps.records.views.ace')
    def test_from_address_set(self, mock_ace):
        """ Verify that the email uses the proper from address """
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_ace.send.call_args[0][0].options['from_address'],
                         self.site_configuration.partner_from_address)

    @patch('credentials.apps.records.views.ace')
    def test_no_full_name(self, mock_ace):
        """ Verify that the email uses the username as a backup for the full name. """
        self.user.full_name = ''
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()

        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_ace.send.call_args[0][0].context['user_full_name'],
                         self.user.username)

    @patch('credentials.apps.records.views.ace')
    def test_from_address_unset(self, mock_ace):
        """ Verify that the email uses the proper default from address """
        self.site_configuration.partner_from_address = None
        self.site_configuration.save()

        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_ace.send.call_args[0][0].options['from_address'],
                         'no-reply@' + self.site.domain)

    def test_email_content_complete(self):
        """Verify an email is actually sent"""
        response = self.post()
        self.assertEqual(response.status_code, 200)
        public_record = ProgramCertRecord.objects.get(user=self.user, program=self.program)
        record_path = reverse('records:public_programs', kwargs={'uuid': public_record.uuid.hex})
        record_link = "http://" + self.site.domain + record_path
        csv_link = urllib.parse.urljoin(record_link, "csv")

        # Check output and make sure it seems correct
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        message = str(email.message())
        self.assertIn(self.program.title + ' Credit Request for', email.subject)
        self.assertIn(self.user.get_full_name() + ' would like to apply for credit in the ' + self.pathway.name,
                      message)
        self.assertIn("has sent their completed program record for", message)
        self.assertIn("<a href=\"" + record_link + "\">View Program Record</a>", message)
        self.assertIn("<a href=\"" + csv_link + "\">Download Record (CSV)</a>", message)
        self.assertEqual(self.site_configuration.partner_from_address, email.from_email)
        self.assertEqual(self.user.email, email.reply_to[0])
        self.assertListEqual([self.pathway.email], email.to)

    def test_email_content_incomplete(self):
        """Verify an email is actually sent"""
        self.user_credential.delete()
        response = self.post()
        self.assertEqual(response.status_code, 200)

        # Check output and make sure it seems correct
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("has sent their partially completed program record for", str(email.message()))

    def prevent_sending_second_email(self):
        """ Verify that an email can't be sent twice """
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user)
        response = self.post()
        self.assertEqual(response.status_code, 400)

    def test_resend_email(self):
        """ Verify that a manually updated email status can be resent """
        UserCreditPathwayFactory(pathway=self.pathway, user=self.user, status='')
        response = self.post()
        self.assertEqual(response.status_code, 200)
        user_credit_pathway = UserCreditPathway.objects.get(user=self.user, pathway=self.pathway)
        self.assertEqual(user_credit_pathway.status, UserCreditPathwayStatus.SENT)


class ProgramRecordCsvViewTests(SiteMixin, TestCase):
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.course = CourseFactory(site=self.site)
        self.course_runs = [CourseRunFactory(course=self.course) for _ in range(3)]
        self.user_grade_low = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                               course_run=self.course_runs[0], letter_grade='A', percent_grade=0.70)
        self.user_grade_high = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                                course_run=self.course_runs[1], letter_grade='C', percent_grade=1.00)
        self.user_grade_revoked_cert = UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                                                        course_run=self.course_runs[2], letter_grade='B',
                                                        percent_grade=.80)
        self.course_certs = [CourseCertificateFactory(course_id=course_run.key, site=self.site)
                             for course_run in self.course_runs]
        self.credential_content_type = ContentType.objects.get(app_label='credentials', model='coursecertificate')
        self.user_credentials = [UserCredentialFactory(username=self.MOCK_USER_DATA['username'],
                                 credential_content_type=self.credential_content_type, credential=course_cert)
                                 for course_cert in self.course_certs]
        self.user_credentials[2].status = UserCredential.REVOKED
        self.org_names = ['CCC', 'AAA', 'BBB']
        self.orgs = [OrganizationFactory(name=name, site=self.site) for name in self.org_names]
        self.program = ProgramFactory(course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site)
        self.program_cert_record = ProgramCertRecordFactory.create(user=self.user, program=self.program)

    @patch('credentials.apps.records.views.SegmentClient', autospec=True)
    def test_404s_with_no_program_cert_record(self, segment_client):  # pylint: disable=unused-argument
        """ Verify that the view 404s if a program cert record isn't found"""
        self.program_cert_record.delete()
        response = self.client.get(reverse(
            'records:program_record_csv',
            kwargs={'uuid': self.program_cert_record.uuid.hex})
        )
        self.assertEqual(404, response.status_code)

    @patch('credentials.apps.records.views.SegmentClient', autospec=True)
    @patch('credentials.apps.records.views.SegmentClient.track', autospec=True)
    def tests_creates_csv(self, segment_client, track):  # pylint: disable=unused-argument
        """ Verify that the csv parses and contains all of the necessary titles/headers"""
        response = self.client.get(
            reverse('records:program_record_csv', kwargs={'uuid': self.program_cert_record.uuid.hex})
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(track.called)
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        body = list(csv_reader)
        metadata_titles = ['Program Name', 'Program Type', 'Platform Provider', 'Authoring Organization(s)',
                           'Learner Name', 'Username', 'Email', '']
        # check the title of each metadata row
        for title in metadata_titles:
            self.assertEqual(title, body.pop(0)[0])
        csv_headers = body.pop(0)
        # Check that the header is present in the response bytestring
        headers = ['course_id', 'percent_grade', 'attempts', 'school', 'issue_date', 'letter_grade', 'name']
        for header in headers:
            self.assertIn(header, csv_headers)

    @patch('credentials.apps.records.views.SegmentClient', autospec=True)
    def test_filename(self, segment_client):  # pylint: disable=unused-argument
        """
        Verify that the filename in response Content-Disposition is utf-8 encoded
        """
        filename = '{username}_{program_name}_grades'.format(
            username=self.user.username,
            program_name=self.program_cert_record.program.title
        )
        filename = filename.replace(' ', '_').lower().encode('utf-8')
        expected = f'attachment; filename="{filename}.csv"'

        response = self.client.get(
            reverse('records:program_record_csv', kwargs={'uuid': self.program_cert_record.uuid.hex})
        )
        actual = response['Content-Disposition']

        self.assertEqual(actual, expected)


@ddt.ddt
class MasqueradeBannerFactoryTests(SiteMixin, TestCase):
    """ Tests for verifying proper loading of the Masquerade Banner Factory. """
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=self.user.username, password=USER_PASSWORD)

    def _render_page(self, page):
        """ Helper method to render the given page with no record/program data. """
        if page == 'records':
            response = self.client.get(reverse('records:index'))
        elif page == 'programs':
            with patch('credentials.apps.records.views.ProgramRecordView._get_record') as get_record:
                get_record.return_value = {}
                response = self.client.get(reverse('records:private_programs', kwargs={'uuid': uuid.uuid4().hex}))

        return response

    @ddt.data('records', 'programs',)
    def test_masquerade_banner_will_appear_for_staff(self, page):
        """ Verify that staff will see the masquerade bar. """
        staff = UserFactory(username='test-staff', is_staff=True)
        self.client.login(username=staff.username, password=USER_PASSWORD)
        response = self._render_page(page)
        self.assertContains(response, 'MasqueradeBannerFactory')

    @ddt.data('records', 'programs',)
    def test_masquerade_banner_will_appear_for_masqueraders(self, page):
        """ Verify that masqueraders will see the masquerade bar. """
        session = self.client.session
        session['is_hijacked_user'] = True
        session.save()
        response = self._render_page(page)
        self.assertContains(response, 'MasqueradeBannerFactory')

    @ddt.data('records', 'programs',)
    def test_masquerade_banner_will_not_appear(self, page):
        """ Verify that the masquerade banner will not appear for other users. """
        response = self._render_page(page)

        self.assertNotContains(response, 'MasqueradeBannerFactory')
