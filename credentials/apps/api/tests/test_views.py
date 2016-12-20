from __future__ import unicode_literals
import json

import ddt
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory
from testfixtures import LogCapture

from credentials.apps.api.serializers import UserCredentialSerializer
from credentials.apps.core.constants import Role
from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests import factories

JSON_CONTENT_TYPE = 'application/json'
LOGGER_NAME = 'credentials.apps.credentials.issuers'
LOGGER_NAME_SERIALIZER = 'credentials.apps.api.serializers'


@ddt.ddt
class BaseUserCredentialViewSetTests(object):
    """ Tests for GenerateCredentialView. """
    # pylint: disable=no-member

    list_path = None

    def setUp(self):
        super(BaseUserCredentialViewSetTests, self).setUp()

        self.user = UserFactory()
        self.client.force_authenticate(self.user)

        self.program_cert = factories.ProgramCertificateFactory()
        self.program_id = self.program_cert.program_id
        self.user_credential = factories.UserCredentialFactory.create(credential=self.program_cert)
        self.user_credential_attribute = factories.UserCredentialAttributeFactory.create(
            user_credential=self.user_credential)
        self.username = "test_user"
        self.request = APIRequestFactory().get('/')

    def _add_permission(self, perm):
        """ DRY helper to add usercredential model permissions to self.user """
        self.user.user_permissions.add(Permission.objects.get(codename='{}_usercredential'.format(perm)))

    def _attempt_update_user_credential(self, data):
        """ Helper method that attempts to patch an existing credential object.

        Arguments:
          data (dict): Data to be converted to JSON and sent to the API.

        Returns:
          Response: HTTP response from the API.
        """
        self._add_permission('change')
        path = reverse("api:v1:usercredential-detail", args=[self.user_credential.id])
        return self.client.patch(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

    def test_get(self):
        """ Verify a single user credential is returned. """
        self._add_permission('view')
        path = reverse("api:v1:usercredential-detail", args=[self.user_credential.id])
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            UserCredentialSerializer(self.user_credential, context={'request': self.request}).data
        )

    def test_list_without_username(self):
        """ Verify a list end point of user credentials will work only with
        username filter. Otherwise it will return 400.
        """
        response = self.client.get(self.list_path)
        self.assertEqual(response.status_code, 400)

    def test_partial_update(self):
        """ Verify that only the 'status' field is updated and other fields
        value remain same.
        """
        data = {
            'id': self.user_credential.id,
            'status': UserCredential.REVOKED,
            'download_url': self.user_credential.download_url + 'test'
        }

        response = self._attempt_update_user_credential(data)
        self.assertEqual(response.status_code, 200)

        user_credential = UserCredential.objects.get(id=self.user_credential.id)
        self.assertEqual(user_credential.status, data["status"])

        self.assertNotEqual(user_credential.download_url, data["download_url"])
        self.assertEqual(user_credential.download_url, self.user_credential.download_url)

    def test_partial_update_authentication(self):
        """ Verify that patch endpoint allows only authorized users to update
        user credential.
        """
        self.client.logout()
        data = {
            "id": self.user_credential.id,
            "download_url": "dummy-url",
        }

        path = reverse("api:v1:usercredential-detail", args=[self.user_credential.id])
        response = self.client.patch(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 401)

    def _attempt_create_user_credentials(self, data):
        """ Helper method that attempts to create user credentials.

        Arguments:
          data (dict): Data to be converted to JSON and sent to the API.

        Returns:
          Response: HTTP response from the API.
        """
        self._add_permission('add')
        path = self.list_path
        return self.client.post(path=path, data=json.dumps(data), content_type=JSON_CONTENT_TYPE)

    @ddt.data(
        ("username", "", "This field may not be blank."),
        ("credential", "", "Credential ID is missing."),
        ("credential", {"program_id": ""}, "Credential ID is missing."),
        ("credential", {"course_id": ""}, "Credential ID is missing."),
    )
    @ddt.unpack
    def test_create_with_empty_fields(self, field_name, value, err_msg):
        """ Verify no UserCredential is created, and HTTP 400 is returned, if
        required fields are missing.
        """
        data = {
            "username": self.username,
            "credential": {"program_id": self.program_id},
            "attributes": [
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                }
            ]
        }
        data.update({field_name: value})
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data.get(field_name),
            [err_msg]
        )

    @ddt.data(
        "username",
        "credential",
        "attributes",
    )
    def test_create_with_missing_fields(self, field_name):
        """ Verify no UserCredential is created, and HTTP 400 is returned, if
        required fields are missing.
        """
        data = {
            "username": self.username,
            "credential": {"program_id": self.program_id},
            "attributes": [
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                }
            ]
        }
        del data[field_name]
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data.get(field_name),
            ['This field is required.']
        )

    def test_create_with_programcertificate(self):
        """ Verify the endpoint supports issuing a new ProgramCertificate credential. """
        program_certificate = factories.ProgramCertificateFactory()
        data = {
            "username": self.username,
            "credential": {
                "program_id": program_certificate.program_id
            },
            "attributes": [
                {
                    "name": self.user_credential_attribute.name,
                    "value": self.user_credential_attribute.value
                },
            ]
        }
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 201)
        user_credential = UserCredential.objects.get(username=self.username)
        self.assertEqual(
            dict(response.data),
            dict(UserCredentialSerializer(user_credential, context={'request': self.request}).data)
        )

    def test_create_authentication(self):
        """ Verify that the create endpoint of user credential does not allow
        the unauthorized users to create a new user credential for the program.
        """
        self.client.logout()
        response = self.client.post(path=self.list_path, data={}, content_type=JSON_CONTENT_TYPE)

        self.assertEqual(response.status_code, 401)

    def test_create_with_duplicate_attributes(self):
        """ Verify no UserCredential is created, and HTTP 400 is returned, if
        there are duplicated attributes.
        """
        data = {
            "username": self.username,
            "credential": {"program_id": self.program_id},
            "attributes": [
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                },
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                },
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                },
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                }
            ]
        }

        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.data, {'attributes': ['Attributes cannot be duplicated.']})

        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserCredential.objects.filter(username=self.username).exists())

    def test_create_with_empty_attributes(self):
        """ Verify no UserCredential is created, and HTTP 400 is returned, if
        there are some attributes are null.
        """
        data = {
            "username": self.username,
            "credential": {"program_id": self.program_id},
            "attributes": [
                {
                    "name": "whitelist_reason",
                    "value": "Reason for whitelisting."
                },
                {
                    "name": "",
                    "value": "Reason for whitelisting."
                }
            ]
        }
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(UserCredential.objects.filter(username=self.username).exists())
        self.assertEqual(
            response.data.get('attributes')[1]['name'][0],
            'This field may not be blank.'
        )

    def test_list_with_username_filter(self):
        """ Verify the list endpoint supports filter data by username."""
        self._add_permission('view')
        factories.UserCredentialFactory(username="dummy-user")
        response = self.client.get(self.list_path, data={'username': self.user_credential.username})
        self.assertEqual(response.status_code, 200)

        # after filtering it is only one related record
        expected = UserCredentialSerializer(
            self.user_credential, context={'request': self.request}
        ).data

        self.assertEqual(response.data, {'count': 1, 'next': None, 'previous': None, 'results': [expected]})

    def test_list_with_status_filter(self):
        """ Verify the list endpoint supports filtering by status."""
        self._add_permission('view')
        factories.UserCredentialFactory.create_batch(2, status="revoked", username=self.user_credential.username)
        response = self.client.get(self.list_path, data={'status': self.user_credential.status})
        self.assertEqual(response.status_code, 400)

        # username and status will return the data.
        response = self.client.get(self.list_path,
                                   data={'username': self.user_credential.username, 'status': UserCredential.AWARDED})

        # after filtering it is only one related record
        expected = UserCredentialSerializer(
            self.user_credential, context={'request': self.request}
        ).data

        self.assertEqual(
            response.data,
            {'count': 1, 'next': None, 'previous': None, 'results': [expected]}
        )

    def test_create_with_non_existing_credential(self):
        """ Verify no UserCredential is created, and HTTP 400 is return if credential
        id does not exists in db.
        """
        cred_id = 10
        data = {
            "username": self.username,
            "credential": {
                "program_id": cred_id
            },
            "attributes": [
            ]
        }

        msg = "Credential ID [{cred_id}] for ProgramCertificate matching query does not exist.".format(
            cred_id=cred_id
        )

        # Verify log is captured.
        with LogCapture(LOGGER_NAME_SERIALIZER) as l:
            response = self._attempt_create_user_credentials(data)
            l.check((LOGGER_NAME_SERIALIZER, 'ERROR', msg))

        self.assertEqual(response.status_code, 400)

    def test_reissue_the_user_credentials(self):
        """ Verify that, if a user has already been issued a credential, further
        attempts to issue the same credential will NOT create a new credential,
        but its attributes will be updated if provided.
        """
        attributes = [
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
            {"name": "grade", "value": "0.85"}
        ]

        data = {
            "username": self.username,
            "credential": {
                "program_id": self.program_cert.program_id
            },
            "attributes": attributes
        }

        # issue first credential for the user
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 201)
        self._assert_usercredential_fields(response, self.username, attributes)

        # change the attributes value
        data["attributes"][0]["value"] = "New reason for whitelisting."
        data["attributes"][1]["value"] = "0.8"

        # try to issue credential again for the same user but with different attribute values and
        # test that the existing record for user credential has been updated with new attribute values
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 201)
        self._assert_usercredential_fields(response, self.username, attributes)

    @ddt.data(
        [{"name": "whitelist_reason", "value": "Reason for whitelisting."}],
        [
            {"name": "whitelist_reason", "value": "Reason for whitelisting."},
            {"name": "grade", "value": "0.85"},
        ],
    )
    def test_create_with_duplicate_attrs(self, attributes):
        """ Verify that, if a user has a credential with attributes
        then its values can be updated.
        """
        # create credential with attributes
        user_credential = factories.UserCredentialFactory.create(
            username=self.username,
            credential=self.program_cert
        )
        factories.UserCredentialAttributeFactory(
            user_credential=user_credential, name="whitelist_reason", value="Reason for whitelisting."
        )
        self.assertTrue(user_credential.attributes.exists())

        data = {
            "username": self.username,
            "credential": {
                "program_id": self.program_id
            },
            "attributes": attributes
        }

        # 2nd attempt to create credential with attributes.
        response = self._attempt_create_user_credentials(data)
        self.assertEqual(response.status_code, 201)
        self._assert_usercredential_fields(response, self.username, attributes)

    def _assert_usercredential_fields(self, response, username, expected_attrs):
        """ Verify the fields on a UserCredential object match expectations. """

        user_credential = UserCredential.objects.filter(username=username)
        self.assertEqual(user_credential.count(), 1)
        self.assertEqual(
            dict(response.data),
            dict(UserCredentialSerializer(
                user_credential[0], context={'request': self.request}
            ).data)
        )

        actual_attributes = [{"name": attr.name, "value": attr.value} for attr in user_credential[0].attributes.all()]
        self.assertEqual(actual_attributes, expected_attrs)

    def test_create_with_in_active_program_certificate(self):
        """ Verify the endpoint throws error if Program is inactive. """
        program_certificate = factories.ProgramCertificateFactory(is_active=False)
        data = {
            "username": self.username,
            "credential": {
                "program_id": program_certificate.program_id
            },
            "attributes": [
                {
                    "name": self.user_credential_attribute.name,
                    "value": self.user_credential_attribute.value
                },
            ]
        }

        msg = "Credential ID [{cred_id}] for ProgramCertificate matching query does not exist.".format(
            cred_id=program_certificate.program_id
        )

        # Verify log is captured.
        with LogCapture(LOGGER_NAME_SERIALIZER) as l:
            response = self._attempt_create_user_credentials(data)
            l.check((LOGGER_NAME_SERIALIZER, 'ERROR', msg))

        self.assertEqual(response.status_code, 400)

    def test_users_lists_access_by_authenticated_users(self):
        """ Verify the list endpoint can be access by authenticated users only."""
        # logout the user
        self.client.logout()
        response = self.client.get(self.list_path, data={'username': self.user_credential.username})
        self.assertEqual(response.status_code, 401)


@ddt.ddt
class BaseUserCredentialViewSetPermissionsTests(object):
    """
    Thoroughly exercise the custom view- and object-level permissions for this viewset.
    """
    # pylint: disable=no-member

    list_path = None

    def make_user(self, group=None, perm=None, **kwargs):
        """ DRY helper to create users with specific groups and/or permissions. """
        user = UserFactory(**kwargs)
        if group:
            user.groups.add(Group.objects.get(name=group))
        if perm:
            user.user_permissions.add(Permission.objects.get(codename='{}_usercredential'.format(perm)))
        return user

    @ddt.data(
        ({'group': Role.ADMINS}, 200),
        ({'perm': 'view'}, 200),
        ({'perm': 'add'}, 404),
        ({'perm': 'change'}, 404),
        ({'username': 'test-user'}, 200),
        ({'username': 'TeSt-uSeR'}, 200),
        ({'username': 'other'}, 404),
    )
    @ddt.unpack
    def test_list(self, user_kwargs, expected_status):
        """
        The list method (GET) requires either 'view' permission, or for the
        'username' query parameter to match that of the requesting user.
        """

        self.client.force_authenticate(self.make_user(**user_kwargs))
        response = self.client.get(self.list_path, {'username': 'test-user'})
        self.assertEqual(response.status_code, expected_status)

    @ddt.data(
        ({'group': Role.ADMINS}, 201),
        ({'perm': 'add'}, 201),
        ({'perm': 'view'}, 403),
        ({'perm': 'change'}, 403),
        ({}, 403),
        ({'username': 'test-user'}, 403),
    )
    @ddt.unpack
    def test_create(self, user_kwargs, expected_status):
        """
        The creation (POST) method requires the 'add' permission.
        """
        program_certificate = factories.ProgramCertificateFactory()
        post_data = {
            'username': 'test-user',
            'credential': {
                'program_id': program_certificate.program_id
            },
            'attributes': [],
        }

        self.client.force_authenticate(self.make_user(**user_kwargs))
        response = self.client.post(self.list_path, data=json.dumps(post_data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, expected_status)

    @ddt.data(
        ({'group': Role.ADMINS}, 200),
        ({'perm': 'view'}, 200),
        ({'perm': 'add'}, 404),
        ({'perm': 'change'}, 404),
        ({'username': 'test-user'}, 200),
        ({'username': 'TeSt-uSeR'}, 200),
        ({'username': 'other-user'}, 404),
    )
    @ddt.unpack
    def test_retrieve(self, user_kwargs, expected_status):
        """
        The retrieve (GET) method requires the 'view' permission, or for the
        requested object to be associated with the username of the requesting
        user.
        """
        program_cert = factories.ProgramCertificateFactory()
        user_credential = factories.UserCredentialFactory.create(credential=program_cert, username='test-user')
        detail_path = reverse("api:v1:usercredential-detail", args=[user_credential.id])

        self.client.force_authenticate(self.make_user(**user_kwargs))
        response = self.client.get(detail_path)
        self.assertEqual(response.status_code, expected_status)

    @ddt.data(
        ({'group': Role.ADMINS}, 200),
        ({'perm': 'view'}, 403),
        ({'perm': 'add'}, 403),
        ({'perm': 'change'}, 200),
        ({'username': 'test-user'}, 403),
        ({}, 403),
    )
    @ddt.unpack
    def test_partial_update(self, user_kwargs, expected_status):
        """
        The partial update (PATCH) method requires the 'change' permission.
        """
        program_cert = factories.ProgramCertificateFactory()
        user_credential = factories.UserCredentialFactory.create(credential=program_cert, username='test-user')
        detail_path = reverse("api:v1:usercredential-detail", args=[user_credential.id])
        post_data = {
            'username': 'test-user',
            'credential': {
                'program_id': program_cert.program_id
            },
            'attributes': [{'name': 'dummy-attr-name', 'value': 'dummy-attr-value'}],
        }
        self.client.force_authenticate(self.make_user(**user_kwargs))
        response = self.client.patch(path=detail_path, data=json.dumps(post_data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, expected_status)


class BaseCourseCredentialViewSetTests(object):
    """ Tests for CourseCredentialViewSetTests. """
    # pylint: disable=no-member

    list_path = None

    def setUp(self):
        super(BaseCourseCredentialViewSetTests, self).setUp()

        self.course_certificate = factories.CourseCertificateFactory()
        self.course_id = self.course_certificate.course_id
        self.user_credential = factories.UserCredentialFactory.create(credential=self.course_certificate)

    def test_list_without_course_id(self):
        """ Verify a list end point of course credentials will work only with
        course_id filter. Otherwise it will return 400.
        """
        self.assert_list_without_id_filter(self.list_path, {
            'error': 'A course_id query string parameter is required for filtering course credentials.'
        })

    def test_list_with_course_id(self):
        """ Verify the list endpoint supports filter data by course_id."""
        course_cert = factories.CourseCertificateFactory(course_id="fake-id")
        factories.UserCredentialFactory.create(credential=course_cert)
        self.assert_list_with_id_filter(data={'course_id': self.course_id})

    def test_list_with_status_filter(self):
        """ Verify the list endpoint supports filtering by status."""
        factories.UserCredentialFactory.create_batch(2, status="revoked", username=self.user_credential.username)
        self.assert_list_with_status_filter(data={'course_id': self.course_id, 'status': UserCredential.AWARDED})

    def test_list_with_certificate_type(self):
        """ Verify the list endpoint supports filtering by certificate_type."""
        course_cert = factories.CourseCertificateFactory(certificate_type="verified")
        factories.UserCredentialFactory.create(credential=course_cert)

        # course_id is mandatory
        response = self.client.get(self.list_path, data={'course_id': self.course_id,
                                                         'certificate_type': self.course_certificate.certificate_type})

        # after filtering it is only one related record
        expected = UserCredentialSerializer(self.user_credential, context={'request': self.request}).data
        self.assertEqual(
            json.loads(response.content),
            {'count': 1, 'next': None, 'previous': None, 'results': [expected]}
        )

    def test_permission_required(self):
        """ Verify that requests require explicit model permissions. """
        self.assert_permission_required({'course_id': self.course_id, 'status': UserCredential.AWARDED})
