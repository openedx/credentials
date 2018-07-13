"""
Tests for records rendering views.
"""
import json
import uuid

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.template.defaultfilters import slugify
from django.template.loader import select_template
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch
from waffle.testutils import override_flag

from credentials.apps.catalog.tests.factories import (CourseFactory, CourseRunFactory, CreditPathwayFactory,
                                                      OrganizationFactory, ProgramFactory)
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.factories import (CourseCertificateFactory, ProgramCertificateFactory,
                                                          UserCredentialFactory)
from credentials.apps.records.models import ProgramCertRecord, UserGrade
from credentials.apps.records.tests.factories import ProgramCertRecordFactory, UserGradeFactory
from credentials.apps.records.tests.utils import dump_random_state

from ..constants import WAFFLE_FLAG_RECORDS

JSON_CONTENT_TYPE = 'application/json'


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
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

        self.assertContains(response, 'My Learner Records')

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
                'completed': True,
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
                'completed': False,
            }
        ]
        self.assertEqual(program_data, expected_program_data)

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
                'completed': False,
            },
            {
                'name': new_program.title,
                'partner': 'TestOrg1, TestOrg2',
                'uuid': new_program.uuid.hex,
                'type': slugify(new_program.type),
                'completed': True,
            }
        ]
        self.assertEqual(program_data, expected_program_data)


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
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
        self.user_credentials = [UserCredentialFactory(username=self.MOCK_USER_DATA['username'],
                                 credential_content_type=self.credential_content_type, credential=course_cert)
                                 for course_cert in self.course_certs]
        self.user_credentials[2].status = UserCredential.REVOKED
        self.org_names = ['CCC', 'AAA', 'BBB']
        self.orgs = [OrganizationFactory(name=name, site=self.site) for name in self.org_names]
        self.program = ProgramFactory(course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site)
        self.pcr = ProgramCertRecordFactory(certificate=ProgramCertificateFactory(program_uuid=self.program.uuid),
                                            user=self.user)

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
        self.assertRegex(response.url, '^/login/.*')  # pylint: disable=deprecated-method

    def test_anonymous_access_public(self):
        """ Verify that the public view does not reject non-logged-in users"""
        self.client.logout()
        response = self.client.get(reverse('records:public_programs', kwargs={'uuid': self.pcr.uuid.hex}))
        self.assertContains(response, 'Record')

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
                          'issue_date': self.user_credentials[1].modified.isoformat(),
                          'percent_grade': self.user_grade_high.percent_grade,
                          'letter_grade': self.user_grade_high.letter_grade, }

        self.assertEqual(grade, expected_grade)

    def test_organization_order(self):
        """ Test that the organizations are returned in the order they were added """
        self.course.owners = self.orgs
        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        program_data = json.loads(response.context_data['record'])['program']
        grade = json.loads(response.context_data['record'])['grades'][0]

        self.assertEqual(program_data['school'], ', '.join(self.org_names))
        self.assertEqual(grade['school'], ', '.join(self.org_names))

    def test_course_run_order(self):
        """ Test that the course_runs are returned in the program order """
        new_course_run = CourseRunFactory()
        self.program.course_runs.add(new_course_run)  # pylint: disable=no-member
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
        """ Adds a course run with no credential and tests that it doesn't appear in the results """
        new_course_run = CourseRunFactory()
        self.program.course_runs.add(new_course_run)  # pylint: disable=no-member
        UserGradeFactory(username=self.MOCK_USER_DATA['username'],
                         course_run=new_course_run, letter_grade='F',
                         percent_grade=.05)
        CourseCertificateFactory(course_id=new_course_run.key, site=self.site)

        response = self.client.get(reverse('records:private_programs', kwargs={'uuid': self.program.uuid.hex}))
        grades = json.loads(response.context_data['record'])['grades']
        self.assertEqual(len(grades), 1)

        self.assertEqual(self.course_runs[1].key, grades[0]['course_id'])

    def test_learner_data(self):
        """ Test that the learner data is returned succesfully """
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
                    'last_updated': UserGrade.objects.last().modified.isoformat(),
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
class ProgramRecordTests(SiteMixin, TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()
        dump_random_state()

        user = UserFactory(username=self.USERNAME)
        self.client.login(username=user.username, password=USER_PASSWORD)
        self.pc = ProgramCertificateFactory(site=self.site)
        self.user_credential = UserCredentialFactory(username=self.USERNAME, credential=self.pc)

    def test_login_required(self):
        """Verify no access without a login"""
        self.client.logout()
        rev = reverse('records:share_program', kwargs={'uuid': self.pc.program_uuid.hex})
        data = {'username': self.USERNAME}
        response = self.client.post(rev, data)
        self.assertEqual(response.status_code, 302)  # redirect to a login page
        self.assertTrue(response.url.startswith('/login/?next='))

    def test_user_creation(self):
        """Verify successful creation of a ProgramCertRecord and return of a uuid"""
        rev = reverse('records:share_program', kwargs={'uuid': self.pc.program_uuid.hex})
        data = {'username': self.USERNAME}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        json_data = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertRegex(json_data['url'], UUID_PATTERN)  # pylint: disable=deprecated-method

    def test_different_user_creation(self):
        """ Verify that the view rejects a User attempting to create a ProgramCertRecord for another """
        diff_username = 'diff-user'
        rev = reverse('records:share_program', kwargs={'uuid': self.pc.program_uuid.hex})
        UserFactory(username=diff_username)
        data = {'username': diff_username}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 403)

    def test_no_user_credential(self):
        """ Verify that the view rejects a User attempting to create a ProgramCertRecord for which they don't
        have the User Credentials """
        pc2 = ProgramCertificateFactory()
        rev = reverse('records:share_program', kwargs={'uuid': pc2.program_uuid.hex})
        data = {'username': self.USERNAME}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 404)

    def test_pcr_already_exists(self):
        """ Verify that the view returns the existing ProgramCertRecord when one already exists for the given username
        and program certificate uuid"""
        rev = reverse('records:share_program', kwargs={'uuid': self.pc.program_uuid.hex})
        data = {'username': self.USERNAME}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        url1 = response.json()['url']
        self.assertEqual(response.status_code, 201)

        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)
        url2 = response.json()['url']
        self.assertEqual(response.status_code, 200)

        self.assertEqual(url1, url2)

    @override_flag(WAFFLE_FLAG_RECORDS, active=False)
    def test_feature_toggle(self):
        """ Verify that the view rejects everyone without the waffle flag. """
        rev = reverse('records:share_program', kwargs={'uuid': self.pc.program_uuid.hex})
        data = {'username': self.USERNAME}
        jdata = json.dumps(data).encode('utf-8')
        response = self.client.post(rev, data=jdata, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(404, response.status_code)


@override_flag(WAFFLE_FLAG_RECORDS, active=True)
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProgramSendTests(SiteMixin, TestCase):
    USERNAME = "test-user"

    def setUp(self):
        super().setUp()

        self.user = UserFactory(username=self.USERNAME)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.program = ProgramFactory(site=self.site)
        self.pathway = CreditPathwayFactory(site=self.site, programs=[self.program])
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
            ProgramCertRecord.objects.get(user=self.user, certificate=self.pc)

        response = self.post()
        self.assertEqual(response.status_code, 200)

        ProgramCertRecord.objects.get(user=self.user, certificate=self.pc)

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
    def test_from_address_unset(self, mock_ace):
        """ Verify that the email uses the proper default from address """
        self.site_configuration.partner_from_address = None
        self.site_configuration.save()

        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_ace.send.call_args[0][0].options['from_address'],
                         'no-reply@' + self.site.domain)  # pylint: disable=no-member

    def test_email_content(self):
        """Verify an email is actually sent"""
        response = self.post()
        self.assertEqual(response.status_code, 200)

        # Check output and make sure it seems correct
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Program Credit Request', email.subject)
        self.assertIn('Please go to the following page', email.body)
        self.assertEqual(self.site_configuration.partner_from_address, email.from_email)
        self.assertListEqual([self.pathway.email], email.to)

    @override_flag(WAFFLE_FLAG_RECORDS, active=False)
    def test_feature_toggle(self):
        """ Verify that the view rejects everyone without the waffle flag. """
        response = self.post()
        self.assertEqual(404, response.status_code)
