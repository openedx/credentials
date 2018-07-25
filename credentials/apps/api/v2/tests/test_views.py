import json
from decimal import Decimal

import ddt
from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APITestCase
from testfixtures import LogCapture

from credentials.apps.api.v2.serializers import (UserCredentialAttributeSerializer, UserCredentialSerializer,
                                                 UserGradeSerializer)
from credentials.apps.api.v2.views import CredentialViewThrottle, GradeViewThrottle
from credentials.apps.catalog.tests.factories import CourseFactory, CourseRunFactory, ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.factories import (CourseCertificateFactory, ProgramCertificateFactory,
                                                          UserCredentialAttributeFactory, UserCredentialFactory)
from credentials.apps.records.models import UserGrade
from credentials.apps.records.tests.factories import UserGradeFactory

JSON_CONTENT_TYPE = 'application/json'
LOGGER_NAME = 'credentials.apps.credentials.issuers'
LOGGER_NAME_SERIALIZER = 'credentials.apps.api.v2.serializers'


# pylint: disable=no-member

@ddt.ddt
class CredentialViewSetTests(SiteMixin, APITestCase):
    list_path = reverse('api:v2:credentials-list')

    def setUp(self):
        super(CredentialViewSetTests, self).setUp()
        self.user = UserFactory()

    def serialize_user_credential(self, user_credential, many=False):
        """ Serialize the given UserCredential object(s). """
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get('/')
        return UserCredentialSerializer(user_credential, context={'request': request}, many=many).data

    def authenticate_user(self, user):
        """ Login as the given user. """
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def add_user_permission(self, user, permission):
        """ Assigns a permission of the given name to the user. """
        user.user_permissions.add(Permission.objects.get(codename=permission))

    def assert_access_denied(self, user, method, path, data=None):
        """ Asserts the given user cannot access the given path via the specified HTTP action/method. """
        self.client.login(username=user.username, password=USER_PASSWORD)
        if data:
            data = json.dumps(data)
        response = getattr(self.client, method)(path, data=data, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def test_authentication(self):
        """ Verify the endpoint requires an authenticated user. """
        self.client.logout()
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 401)

        superuser = UserFactory(is_staff=True, is_superuser=True)
        self.authenticate_user(superuser)
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 200)

    def test_create(self):
        program_certificate = ProgramCertificateFactory(site=self.site)
        expected_username = 'test_user'
        expected_attribute_name = 'fake-name'
        expected_attribute_value = 'fake-value'
        data = {
            'username': expected_username,
            'credential': {
                'program_uuid': str(program_certificate.program_uuid)
            },
            'status': 'awarded',
            'attributes': [
                {
                    'name': expected_attribute_name,
                    'value': expected_attribute_value,
                }
            ],
        }

        # Verify users without the add permission are denied access
        self.assert_access_denied(self.user, 'post', self.list_path, data=data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usercredential')
        response = self.client.post(self.list_path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        user_credential = UserCredential.objects.last()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_credential(user_credential))

        self.assertEqual(user_credential.username, expected_username)
        self.assertEqual(user_credential.credential, program_certificate)
        self.assertEqual(user_credential.attributes.count(), 1)

        attribute = user_credential.attributes.first()
        self.assertEqual(attribute.name, expected_attribute_name)
        self.assertEqual(attribute.value, expected_attribute_value)

    def test_create_with_duplicate_attributes(self):
        """ Verify an error is returned if an attempt is made to create a UserCredential with multiple attributes
        of the same name. """
        program_certificate = ProgramCertificateFactory(site=self.site)
        data = {
            'username': 'test-user',
            'credential': {
                'program_uuid': str(program_certificate.program_uuid)
            },
            'attributes': [
                {
                    'name': 'attr-name',
                    'value': 'attr-value',
                },
                {
                    'name': 'attr-name',
                    'value': 'another-attr-value',
                }
            ],
        }

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usercredential')
        response = self.client.post(self.list_path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'attributes': ['Attribute names cannot be duplicated.']})

    def test_create_with_existing_user_credential(self):
        """ Verify that, if a user has already been issued a credential, further attempts to issue the same credential
        will NOT create a new credential, but update the attributes of the existing credential.
        """
        user_credential = UserCredentialFactory(credential__site=self.site)
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usercredential')

        # POSTing the exact data that exists in the database should not change the UserCredential
        data = self.serialize_user_credential(user_credential)
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

        # POSTing with modified status/attributes should update the existing UserCredential
        data = self.serialize_user_credential(user_credential)
        expected_attribute = UserCredentialAttributeFactory.build()
        data['status'] = 'revoked'
        data['attributes'] = [
            UserCredentialAttributeSerializer(expected_attribute).data
        ]
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

        user_credential.refresh_from_db()
        self.assertEqual(response.data, self.serialize_user_credential(user_credential))
        self.assertEqual(user_credential.attributes.count(), 1)

        actual_attribute = user_credential.attributes.first()
        self.assertEqual(actual_attribute.name, expected_attribute.name)
        self.assertEqual(actual_attribute.value, expected_attribute.value)

    def test_destroy(self):
        """ Verify the endpoint does NOT support the DELETE operation. """
        credential = UserCredentialFactory(
            credential__site=self.site,
            status=UserCredential.AWARDED,
            username=self.user.username
        )
        path = reverse('api:v2:credentials-detail', kwargs={'uuid': credential.uuid})

        # Verify users without the view permission are denied access
        self.assert_access_denied(self.user, 'delete', path)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'delete_usercredential')
        response = self.client.delete(path)
        credential.refresh_from_db()

        self.assertEqual(credential.status, UserCredential.REVOKED)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.serialize_user_credential(credential))

    def test_retrieve(self):
        """ Verify the endpoint returns data for a single UserCredential. """
        credential = UserCredentialFactory(
            credential__site=self.site,
            username=self.user.username
        )
        path = reverse('api:v2:credentials-detail', kwargs={'uuid': credential.uuid})

        # Verify users without the view permission are denied access
        self.assert_access_denied(self.user, 'get', path)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.serialize_user_credential(credential))

    def test_list(self):
        """ Verify the endpoint returns data for multiple UserCredentials. """
        # Verify users without the view permission are denied access
        self.assert_access_denied(self.user, 'get', self.list_path)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['results'],
            self.serialize_user_credential(UserCredential.objects.all(), many=True)
        )

    def test_list_status_filtering(self):
        """ Verify the endpoint returns data for all UserCredentials that match the specified status. """
        awarded = UserCredentialFactory.create_batch(3, credential__site=self.site, status=UserCredential.AWARDED)
        revoked = UserCredentialFactory.create_batch(3, credential__site=self.site, status=UserCredential.REVOKED)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')

        for status, expected in (('awarded', awarded), ('revoked', revoked)):
            response = self.client.get(self.list_path + '?status={}'.format(status))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['results'], self.serialize_user_credential(expected, many=True))

    def assert_list_username_filter_request_succeeds(self, username, expected):
        """ Asserts the logged in user can list credentials for a specific user. """
        response = self.client.get(self.list_path + '?username={}'.format(username))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], self.serialize_user_credential(expected, many=True))

    def test_list_username_filtering(self):
        """ Verify the endpoint returns data for all UserCredentials awarded to the user matching the username. """
        UserCredentialFactory.create_batch(3, credential__site=self.site)

        self.authenticate_user(self.user)

        # Users should be able to view their own credentials without additional permissions
        username = self.user.username
        expected = UserCredentialFactory.create_batch(3, credential__site=self.site, username=username)
        self.assert_list_username_filter_request_succeeds(username, expected)

        # Privileged users should be able to view all credentials
        username = 'test_user'
        expected = UserCredentialFactory.create_batch(3, credential__site=self.site, username=username)
        self.add_user_permission(self.user, 'view_usercredential')

        self.assert_list_username_filter_request_succeeds(username, expected)

    def test_list_program_uuid_filtering(self):
        """ Verify the endpoint returns data for all UserCredentials in the given program. """

        # Course run 1 is in a program, course run 2 is not
        course1_run = CourseRunFactory()
        course2_run = CourseRunFactory()
        program = ProgramFactory(course_runs=[course1_run])

        program_certificate = ProgramCertificateFactory(site=self.site, program_uuid=program.uuid)
        course1_certificate = CourseCertificateFactory(site=self.site, course_id=course1_run.key)
        course2_certificate = CourseCertificateFactory(site=self.site, course_id=course2_run.key)

        # Create some credentials related to the program
        course1_cred = UserCredentialFactory(credential=course1_certificate)
        program_creds = UserCredentialFactory.create_batch(3, credential=program_certificate)
        expected = [course1_cred] + program_creds

        # Create some more credentials that we don't expect to see returned
        UserCredentialFactory.create_batch(3)
        UserCredentialFactory(credential=course2_certificate)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')

        response = self.client.get(self.list_path + '?program_uuid={}'.format(program.uuid))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], self.serialize_user_credential(expected, many=True))

    def test_list_type_filtering(self):
        """ Verify the endpoint returns data for all UserCredentials for the given type. """
        program_certificate = ProgramCertificateFactory(site=self.site)
        course_certificate = CourseCertificateFactory(site=self.site)

        course_cred = UserCredentialFactory(credential=course_certificate)
        program_cred = UserCredentialFactory(credential=program_certificate)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')

        response = self.client.get(self.list_path + '?type=course-run')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], self.serialize_user_credential([course_cred], many=True))

        response = self.client.get(self.list_path + '?type=program')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], self.serialize_user_credential([program_cred], many=True))

    @ddt.data('put', 'patch')
    def test_update(self, method):
        """ Verify the endpoint supports updating the status of a UserCredential, but no other fields. """
        credential = UserCredentialFactory(
            credential__site=self.site,
            username=self.user.username
        )
        path = reverse('api:v2:credentials-detail', kwargs={'uuid': credential.uuid})
        expected_status = UserCredential.REVOKED
        data = {'status': expected_status}

        # Verify users without the change permission are denied access
        self.assert_access_denied(self.user, method, path, data=data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'change_usercredential')
        response = getattr(self.client, method)(path, data=data)
        credential.refresh_from_db()

        self.assertEqual(credential.status, expected_status)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.serialize_user_credential(credential))

    def test_site_filtering(self):
        """ Verify the endpoint only returns credentials linked to a single site. """
        credential = UserCredentialFactory(credential__site=self.site)
        UserCredentialFactory()

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')

        self.assertEqual(UserCredential.objects.count(), 2)

        response = self.client.get(self.list_path)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0], self.serialize_user_credential(credential))


@ddt.ddt
class GradeViewSetTests(SiteMixin, APITestCase):
    list_path = reverse('api:v2:grades-list')

    def setUp(self):
        super(GradeViewSetTests, self).setUp()
        self.user = UserFactory()
        self.course = CourseFactory(site=self.site)
        self.course_run = CourseRunFactory(course=self.course)
        self.data = {
            'username': 'test_user',
            'course_run': self.course_run.key,
            'letter_grade': 'A',
            'percent_grade': 0.9,
            'verified': True,
        }

    def serialize_user_grade(self, user_grade, many=False):
        """ Serialize the given UserGrade object(s). """
        request = APIRequestFactory(SERVER_NAME=self.site.domain).get('/')
        return UserGradeSerializer(user_grade, context={'request': request}, many=many).data

    def authenticate_user(self, user):
        """ Login as the given user. """
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def add_user_permission(self, user, permission):
        """ Assigns a permission of the given name to the user. """
        user.user_permissions.add(Permission.objects.get(codename=permission))

    def assert_access_denied(self, user, method, path, data=None):
        """ Asserts the given user cannot access the given path via the specified HTTP action/method. """
        self.client.login(username=user.username, password=USER_PASSWORD)
        if data:
            data = json.dumps(data)
        response = getattr(self.client, method)(path, data=data, content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def test_authentication(self):
        """ Verify the endpoint requires an authenticated user. """
        self.client.logout()
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

        superuser = UserFactory(is_staff=True, is_superuser=True)
        self.authenticate_user(superuser)
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

    def test_create(self):
        # Verify users without the add permission are denied access
        self.assert_access_denied(self.user, 'post', self.list_path, data=self.data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usergrade')
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        grade = UserGrade.objects.last()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(grade))

        self.assertEqual(grade.username, self.data['username'])
        self.assertTrue(grade.verified)
        self.assertEqual(grade.letter_grade, self.data['letter_grade'])
        self.assertEqual(grade.percent_grade, Decimal('0.9'))
        self.assertEqual(grade.course_run, self.course_run)

    def test_create_with_empty_letter_grade(self):
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usergrade')

        # Empty value
        self.data['username'] = 'empty'
        self.data['letter_grade'] = ''
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(UserGrade.objects.last()))

        # No value
        self.data['username'] = 'noexist'
        del self.data['letter_grade']
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(UserGrade.objects.last()))

        # Null value
        self.data['username'] = 'null'
        self.data['letter_grade'] = None
        response = self.client.post(self.list_path, data=json.dumps(self.data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_grade(UserGrade.objects.last()))

    def test_create_with_existing_user_grade(self):
        """ Verify that, if a user has already been issued a grade, further attempts to issue the same grade
        will NOT create a new grade, but update the fields of the existing grade.
        """
        grade = UserGradeFactory(course_run=self.course_run)
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usergrade')

        # POSTing with modified data should update the existing UserGrade
        data = self.serialize_user_grade(grade)
        data['letter_grade'] = 'B'
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)

        grade.refresh_from_db()
        self.assertEqual(grade.letter_grade, 'B')
        self.assertDictEqual(response.data, self.serialize_user_grade(grade))

    @ddt.data('put', 'patch')
    def test_update(self, method):
        """ Verify the endpoint supports updating the status of a UserGrade, but no other fields. """
        grade = UserGradeFactory(
            course_run=self.course_run,
            username=self.user.username,
            letter_grade='C',
        )
        path = reverse('api:v2:grades-detail', kwargs={'pk': grade.id})

        # Verify users without the change permission are denied access
        self.assert_access_denied(self.user, method, path, data=self.data)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'change_usergrade')
        response = getattr(self.client, method)(path, data=self.data)

        grade.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(grade.letter_grade, self.data['letter_grade'])
        self.assertDictEqual(response.data, self.serialize_user_grade(grade))


class ThrottlingTests(SiteMixin, APITestCase):
    """ Tests for throttling the credentials api endpoints """

    def setUp(self):
        super(ThrottlingTests, self).setUp()
        self.user = UserFactory()

    def authenticate_user(self, user):
        """ Login as the given user. """
        self.client.logout()
        self.client.login(username=user.username, password=USER_PASSWORD)

    def add_user_permission(self, user, permission):
        """ Assigns a permission of the given name to the user. """
        user.user_permissions.add(Permission.objects.get(codename=permission))

    def assert_throttling_log_correct(self, log_capture, view_set):
        """ Helper for testing correct log output for throttling. """
        log_capture.check(
            (
                'credentials.apps.api.v2.views',
                'WARNING',
                'Credentials API endpoint {} is being throttled.'.format(view_set)
            )
        )

    def test_credential_view_throttling(self):
        """
        Verify requests are throttled and a message is logged after limit.

        Note: There is a potential for this test to be flaky in the case the
        endpoint we are testing slows down over time and/or the rate limit is
        increased.
        """
        with LogCapture() as log:
            throttle = CredentialViewThrottle()
            list_path = reverse('api:v2:credentials-list')
            self.authenticate_user(self.user)
            self.add_user_permission(self.user, 'view_usercredential')

            rate_limit, _ = throttle.parse_rate(throttle.get_rate())
            # All requests up to the rate limit should be acceptable
            for _ in range(0, rate_limit):
                response = self.client.get(list_path)
                self.assertEqual(response.status_code, 200)

            # Request after limit should NOT be acceptable
            response = self.client.get(list_path)
            self.assertEqual(response.status_code, 429)
            self.assert_throttling_log_correct(log, 'CredentialViewSet')

    def test_grade_view_throttling(self):
        """
        Verify requests are throttled and a message is logged after limit.

        Note: There is a potential for this test to be flaky in the case the
        endpoint we are testing slows down over time and/or the rate limit is
        increased.
        """
        with LogCapture() as log:
            throttle = GradeViewThrottle()
            course = CourseFactory(site=self.site)
            course_run = CourseRunFactory(course=course)
            data = {
                'username': 'test_user',
                'course_run': course_run.key,
                'letter_grade': 'A',
                'percent_grade': 0.9,
                'verified': True,
            }
            grade = UserGradeFactory(
                course_run=course_run,
                username=self.user.username,
                letter_grade='C',
            )
            path = reverse('api:v2:grades-detail', kwargs={'pk': grade.id})

            self.authenticate_user(self.user)
            self.add_user_permission(self.user, 'change_usergrade')

            rate_limit, _ = throttle.parse_rate(throttle.get_rate())
            # All requests up to the rate limit should be acceptable
            for _ in range(0, rate_limit):
                response = getattr(self.client, 'put')(path, data=data)
                self.assertEqual(response.status_code, 200)

            # Request after limit should NOT be acceptable
            response = getattr(self.client, 'put')(path, data=data)
            self.assertEqual(response.status_code, 429)
            self.assert_throttling_log_correct(log, 'GradeViewSet')
