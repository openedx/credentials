import json

import ddt
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APITestCase
from waffle.models import Switch

from credentials.apps.api.v2.serializers import UserCredentialAttributeSerializer, UserCredentialSerializer
from credentials.apps.api.v2.views import DISABLE_API_SITE_FILTERING_SWITCH_NAME
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.factories import (
    ProgramCertificateFactory, UserCredentialAttributeFactory, UserCredentialFactory
)

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
        Switch.objects.update_or_create(name=DISABLE_API_SITE_FILTERING_SWITCH_NAME, defaults={'active': False})

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
        program_certificate = ProgramCertificateFactory()
        expected_username = 'test_user'
        expected_attribute_name = 'fake-name'
        expected_attribute_value = 'fake-value'
        data = {
            'username': expected_username,
            'credential': {
                'program_uuid': str(program_certificate.program_uuid)
            },
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
        program_certificate = ProgramCertificateFactory()
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
        user_credential = UserCredentialFactory()
        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'add_usercredential')

        # POSTing the exact data that exists in the database should not change the UserCredential
        data = self.serialize_user_credential(user_credential)
        response = self.client.post(self.list_path, data=JSONRenderer().render(data), content_type=JSON_CONTENT_TYPE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.serialize_user_credential(user_credential))

        # POSTing with modified attributes should update the attributes of the existing UserCredential
        data = self.serialize_user_credential(user_credential)
        expected_attribute = UserCredentialAttributeFactory.build()
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
        username = 'test_user'  # pylint: disable=redefined-variable-type
        expected = UserCredentialFactory.create_batch(3, credential__site=self.site, username=username)
        self.add_user_permission(self.user, 'view_usercredential')

        self.assert_list_username_filter_request_succeeds(username, expected)

    def test_list_program_uuid_filtering(self):
        """ Verify the endpoint returns data for all UserCredentials awarded for the given program. """
        UserCredentialFactory.create_batch(3)
        program_certificate = ProgramCertificateFactory(site=self.site)
        expected = UserCredentialFactory.create_batch(3, credential=program_certificate)

        self.authenticate_user(self.user)
        self.add_user_permission(self.user, 'view_usercredential')

        response = self.client.get(self.list_path + '?program_uuid={}'.format(program_certificate.program_uuid))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'], self.serialize_user_credential(expected, many=True))

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

        # Verify switch *disabling* site filtering disables site filtering
        Switch.objects.update_or_create(name=DISABLE_API_SITE_FILTERING_SWITCH_NAME, defaults={'active': True})
        response = self.client.get(self.list_path)
        self.assertEqual(response.data['count'], 2)
