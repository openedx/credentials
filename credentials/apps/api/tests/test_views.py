"""
Tests for credentials service views.
"""
from __future__ import unicode_literals
import json

from django.db import IntegrityError
from django.core.urlresolvers import reverse
from mock import patch
from rest_framework.test import APITestCase, APITransactionTestCase
from testfixtures import LogCapture

from credentials.apps.api.tests.mixin import AuthClientMixin
from credentials.apps.api import serializers
from credentials.apps.api.tests.factories import (
    CourseCertificateFactory, ProgramCertificateFactory,
    UserCredentialFactory, UserCredentialAttributeFactory
)
from credentials.apps.credentials.constants import DRF_DATE_FORMAT
from credentials.apps.credentials.models import UserCredential, UserCredentialAttribute


JSON_CONTENT_TYPE = 'application/json'
LOGGER_NAME = 'credentials.apps.credentials.issuers'


class TestGenerateProgramsCredentialView(AuthClientMixin, APITestCase):
    """ Tests for ProgramsCredentialView. """

    def setUp(self):
        super(TestGenerateProgramsCredentialView, self).setUp()

        # api client with no permissions
        self.client = self.get_api_client(permission_code=None)

        # create credentials for user
        self.program_cert = ProgramCertificateFactory.create()
        self.program_id = self.program_cert.program_id
        self.user_credential = UserCredentialFactory.create(credential=self.program_cert)
        self.attr = UserCredentialAttributeFactory.create(user_credential=self.user_credential)

    def _create_output_data(self, credential, program):
        """ Helper method to generate user credential api response data. """

        attrs = credential.attributes.all()
        expected_credential = {
            "id": credential.id,
            "username": credential.username,
            "credential": {
                "credential_id": credential.credential_id,
                "program_id": program.program_id
            },
            "status": "awarded",
            "download_url": credential.download_url,
            "uuid": str(credential.uuid),
            "attributes": self._create_attrs(attrs),
            "created": credential.created.strftime(DRF_DATE_FORMAT),
            "modified": credential.modified.strftime(DRF_DATE_FORMAT)
        }
        return expected_credential

    def _create_attrs(self, attrs):
        """ Helper method to generate user attributes data. """
        ls = []
        for attr in attrs:
            ls.append(
                {
                    "namespace": attr.namespace,
                    "name": attr.name,
                    "value": attr.value
                }
            )
        return ls

    def _attempt_update_user_credential(self, data):
        """ Helper method that attempts to patch an existing credential object.

        Arguments:
          data (dict): Data to be converted to JSON and sent to the API.

        Returns:
          Response: HTTP response from the API.
        """
        # get client with user has permission to change user credential
        client = self.get_api_client(permission_code="change_usercredential")
        path = reverse("credentials:v1:usercredential-detail", args=[self.user_credential.id])
        return client.patch(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

    def test_get_user_credential(self):
        """ Verify a single user credential is returned. """

        path = reverse("credentials:v1:usercredential-detail", args=[self.user_credential.id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            json.loads(response.content),
            self._create_output_data(self.user_credential, self.program_cert)
        )

    def test_list_credentials_without_user(self):
        """ Verify a list end point of user credentials will work only with
        username filter. Otherwise it will return 400.
        """
        response = self.client.get(path=reverse("credentials:v1:usercredential-list"))
        self.assertEqual(response.status_code, 400)

    def test_patch_user_credentials(self):
        """ Verify that status of credentials will be updated with patch request. """
        data = {
            "id": self.user_credential.id,
            "status": "revoked",
        }
        response = self._attempt_update_user_credential(data)
        self.assertEqual(json.loads(response.content)['status'], data['status'])

    def test_patch_only_status(self):
        """ Verify that users allow to update only status of credentials will
        be updated with patch request.
        """
        data = {
            "id": self.user_credential.id,
            "download_url": "dummy-url",
        }
        response = self._attempt_update_user_credential(data)

        self.assertDictEqual(
            json.loads(response.content),
            {'error': 'Only status of credential is allowed to update'}
        )

    def test_permissions_for_patch(self):
        """ Verify that patch endpoint allows only authorized users to update
        user credential.
        """

        data = {
            "id": self.user_credential.id,
            "download_url": "dummy-url",
        }

        path = reverse("credentials:v1:usercredential-detail", args=[self.user_credential.id])
        response = self.client.patch(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 403)

    def _attempt_create_user_credentials(self, data):
        """ Helper method that attempts to create user credentials.

        Arguments:
          data (dict): Data to be converted to JSON and sent to the API.

        Returns:
          Response: HTTP response from the API.
        """
        # get client with user has permission to add user credential
        client = self.get_api_client(permission_code="add_usercredential")
        path = reverse("credentials:v1:usercredential-list")
        return client.post(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

    def test_create_user_credential_for_program(self):
        """ Verify the endpoint supports the creation of new user credential for program. """

        program_2 = ProgramCertificateFactory.create(program_id=100)
        username = 'user2'
        data = {
            "username": username,
            "program_id": program_2.program_id,
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 200)
        users_creds = UserCredential.objects.filter(username=username)
        expected_data = self._create_output_data(users_creds[0], program_2)
        self.assertDictEqual(json.loads(response.content), expected_data)

    def test_permissions_for_create(self):
        """ Verify that the create endpoint of user credential does not allow
        the unauthorized users to create a new user credential for the program.
        """

        username = 'user2'
        data = {
            "username": username,
            "program_id": self.program_id,
            "attributes": [
            ]
        }
        path = reverse("credentials:v1:usercredential-list")
        response = self.client.post(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 403)

    def test_create_user_credential_for_course(self):
        """ Verify the endpoint doest not support creation of new user credential
        for course as we don't have issuer implemented for course certificate.
        """

        course_cert = CourseCertificateFactory.create(course_id='dummy-id')
        username = 'user2'
        data = {
            "username": username,
            "course_id": course_cert.course_id,
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserCredential.objects.filter(username=username).exists())

    def test_without_program_id(self):
        """ Verify that create endpoint return 400-Bad Request with program_id. """
        data = {
            "username": "user1",
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {"error": "Credential type is missing."})

    def test_with_invalid_type_of_program_id(self):
        """ Verify that create endpoint returns 400-Bad Request with no program_id is provided
        or program id is not a valid int.
        """

        data = {
            "username": "user1",
            "program_id": "0000",
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {"error": "Credential Id [0000] is invalid."})

    def test_create_with_invalid_program_id(self):
        """ Verify that create endpoint returns error on invalid program id. """

        data = {
            "username": "user1",
            "program_id": 900,
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserCredential.objects.filter(username='user1').exists())

    def test_create_without_username(self):
        """ Verify that create endpoint return 400-Bad Request without username. """

        data = {
            "program_id": self.program_id,
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {"error": "Username is not available."})

    def test_create_credential_with_duplicate_attributes(self):
        """ Verify in case of duplicate attributes User credential
        object will not create and not any attribute.
        ('user_credential', 'namespace', 'name')
        """
        username = 'test_user'
        data = {
            "username": username,
            "program_id": self.program_id,
            "attributes": [
                {
                    "namespace": "white",
                    "name": "grade",
                    "value": "0.5"
                },
                {
                    "namespace": "dummyspace",
                    "name": "grade",
                    "value": "0.6"
                },
                {
                    "namespace": "white",
                    "name": "grade",
                    "value": "0.7"
                },
                {
                    "namespace": "white",
                    "name": "grade",
                    "value": "0.8"
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserCredential.objects.filter(username=username).exists())

    def test_existing_credential_not_add_or_update_attributes(self):
        """ Verify that if credential already exists then during recreation attempt
        for same user credential with attributes will neither create or update the credential and
        its attributes.
        """
        username = 'test_user'
        data = {
            "username": username,
            "program_id": self.program_id,
            "attributes": [
            ]
        }

        data_1 = {
            "username": username,
            "program_id": self.program_id,
            "attributes": [
                {
                    "namespace": "white",
                    "name": "grade",
                    "value": "0.5"
                }
            ]
        }

        # create first credential without attributes.
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 200)

        user_cred_1 = UserCredential.objects.get(username=username)
        self.assertDictEqual(
            json.loads(response.content),
            self._create_output_data(user_cred_1, self.program_cert)
        )
        self.assertEqual(user_cred_1.attributes.all().count(), 0)

        # 2nd attempt to create credential with attributes.
        msg = 'User [{username}] already has a credential for program [{program_id}].'.format(
            username=username,
            program_id=self.program_id
        )

        # Verify log is captured.
        with LogCapture(LOGGER_NAME) as l:
            response = self._attempt_create_user_credentials(data_1)
            l.check((LOGGER_NAME, 'WARNING', msg))
            self.assertEqual(response.status_code, 200)

        user_cred_2 = UserCredential.objects.get(username=username)
        self.assertEqual(user_cred_2.attributes.all().count(), 0)

        # both objects are equal
        self.assertEqual(user_cred_1, user_cred_2)

    def test_username_filter(self):
        """ Test api's with username filter."""
        path = reverse("credentials:v1:usercredential-list") + "?username={}".format(
            self.user_credential.username)

        # check query count for username filter
        with self.assertNumQueries(4):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)

        expected_json = self._create_output_data(self.user_credential, self.program_cert)
        self.assertDictEqual(
            json.loads(response.content),
            {'count': 1, 'next': None, 'previous': None, 'results': [expected_json]}
        )

    def test_status_filter_with_username(self):
        """ Test api's with status filter will work only with username."""
        # without username it will return 400 error code.
        path = reverse("credentials:v1:usercredential-list") + "?status={}".format(
            self.user_credential.status)

        response = self.client.get(path)
        self.assertEqual(response.status_code, 400)

        # username and status will return the data.
        path = reverse("credentials:v1:usercredential-list") + "?username={user}&status={status}".format(
            user=self.user_credential.username,
            status=UserCredential.AWARDED)
        response = self.client.get(path)

        expected_json = self._create_output_data(self.user_credential, self.program_cert)
        self.assertDictEqual(
            json.loads(response.content),
            {'count': 1, 'next': None, 'previous': None, 'results': [expected_json]}
        )

    def test_create_method_queries(self):
        """ Verify the number of queries during the create credential. """

        program_2 = ProgramCertificateFactory.create(program_id=100)
        username = 'user2'
        data = {
            "username": username,
            "program_id": program_2.program_id,
            "attributes": [
                {
                    "namespace": self.attr.namespace,
                    "name": self.attr.name,
                    "value": self.attr.value
                },
                {
                    "namespace": 'second',
                    "name": 'testing',
                    "value": '10'
                }
            ]
        }
        client = self.get_api_client(permission_code="add_usercredential")

        with self.assertNumQueries(12):
            path = reverse("credentials:v1:usercredential-list")
            response = client.post(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

        users_creds = UserCredential.objects.filter(username=username)
        expected_data = self._create_output_data(users_creds[0], program_2)
        self.assertDictEqual(json.loads(response.content), expected_data)


class TestAPITransactions(AuthClientMixin, APITransactionTestCase):
    """
    Tests the transactional behavior of the user credential API
    """
    test_password = "test"

    def setUp(self):
        super(TestAPITransactions, self).setUp()
        self.program_cre = ProgramCertificateFactory.create()
        self.program_id = self.program_cre.program_id

    def test_create_credential_api_rollback(self):
        """
        Verify that credential api is transactional in case of any failure
        all data will be rollback. If try to create attribute with duplicate
        namespace and name then unique constraint will trigger and
        user-credential object will roll back.
        """
        username = 'test_user'
        data = {
            "username": username,
            "program_id": self.program_id,
            "attributes": [
                {
                    "namespace": "white",
                    "name": "grade",
                    "value": "0.5"
                },
                {
                    "namespace": "white",
                    "name": "grade",
                    "value": "0.8"
                }
            ]
        }

        path = reverse("credentials:v1:usercredential-list")
        # mock the models's get_or_create method to raise the integrity error.
        # so the user-credential object roll back.
        with patch.object(UserCredentialAttribute.objects, "get_or_create") as mock_get_or_create:
            mock_get_or_create.side_effect = IntegrityError
            __ = self.client.post(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
            self.assertEqual(UserCredential.objects.all().count(), 0)


class TestProgramsView(AuthClientMixin, APITestCase):
    """ Tests for ProgramsView. """

    def setUp(self):
        super(TestProgramsView, self).setUp()

        # api client with no permissions
        self.client = self.get_api_client(permission_code=None)

        # create credentials for user
        self.program_cre = ProgramCertificateFactory.create()
        self.program_id = self.program_cre.program_id
        self.user_credential = UserCredentialFactory.create(credential=self.program_cre)
        self.attr = UserCredentialAttributeFactory.create(user_credential=self.user_credential)

    def test_list_programs_credential(self):
        """ Verify a list end point of programs credentials return list of
        credentials.
        """
        dummy_program_cert = ProgramCertificateFactory.create()
        dummy_user_credential = UserCredentialFactory.create(credential=dummy_program_cert)

        response = self.client.get(path=reverse("credentials:v1:programcertificate-list"))
        self.assertEqual(response.status_code, 200)
        results = [
            {
                "user_credential": [
                    serializers.UserCredentialSerializer(self.user_credential).data,
                ],
                "program_id": self.program_id
            },
            {
                "user_credential": [
                    serializers.UserCredentialSerializer(dummy_user_credential).data,
                ],
                "program_id": dummy_program_cert.program_id
            }
        ]

        expected = {'count': 2, 'next': None, 'previous': None, 'results': results}
        self.assertDictEqual(json.loads(response.content), expected)


class TestCourseView(AuthClientMixin, APITestCase):
    """ Tests for ProgramsView. """

    def setUp(self):
        super(TestCourseView, self).setUp()

        # api client with no permissions
        self.client = self.get_api_client(permission_code=None)

        # create credentials for user
        self.course_cre = CourseCertificateFactory.create()
        self.course_id = self.course_cre.course_id
        self.user_credential = UserCredentialFactory.create(credential=self.course_cre)
        self.attr = UserCredentialAttributeFactory.create(user_credential=self.user_credential)

    def test_list_programs_credential(self):
        """ Verify a list end point of course credentials return list of
        credentials.
        """
        course_cre2 = CourseCertificateFactory.create()
        user_credential2 = UserCredentialFactory.create(credential=course_cre2)

        response = self.client.get(path=reverse("credentials:v1:coursecertificate-list"))
        self.assertEqual(response.status_code, 200)
        results = [
            {
                "user_credential": [
                    serializers.UserCredentialSerializer(self.user_credential).data,
                ],
                "course_id": self.course_cre.course_id,
                "certificate_type": self.course_cre.certificate_type
            },
            {
                "user_credential": [
                    serializers.UserCredentialSerializer(user_credential2).data,
                ],
                "course_id": course_cre2.course_id,
                "certificate_type": course_cre2.certificate_type
            }
        ]

        expected = {'count': 2, 'next': None, 'previous': None, 'results': results}
        self.assertDictEqual(json.loads(response.content), expected)
