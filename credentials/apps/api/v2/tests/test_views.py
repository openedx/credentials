"""
Tests for credentials service views.
"""
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from credentials.apps.api.tests.mixins import CredentialViewSetTestsMixin
from credentials.apps.api.tests.test_views import (
    BaseUserCredentialViewSetTests, BaseUserCredentialViewSetPermissionsTests, BaseCourseCredentialViewSetTests,
)
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests import factories

JSON_CONTENT_TYPE = 'application/json'
LOGGER_NAME = 'credentials.apps.credentials.issuers'
LOGGER_NAME_SERIALIZER = 'credentials.apps.api.serializers'


class ProgramCredentialViewSetTests(CredentialViewSetTestsMixin, APITestCase):
    """ Tests for ProgramCredentialViewSetTests. """

    list_path = reverse("api:v2:programcredential-list")

    def setUp(self):
        super(ProgramCredentialViewSetTests, self).setUp()

        self.program_certificate = factories.ProgramCertificateFactory()
        self.program_id = self.program_certificate.program_id
        self.program_uuid = self.program_certificate.program_uuid
        self.user_credential = factories.UserCredentialFactory.create(credential=self.program_certificate)
        self.request = APIRequestFactory().get('/')

    def test_list_without_uuid(self):
        """ Verify a list end point of program credentials will work with
        program_uuid filter.
        """
        error_message = {'error': 'A UUID query string parameter is required for filtering program credentials.'}
        self.assert_list_without_id_filter(path=self.list_path, expected=error_message)

    def test_list_without_uuid_but_with_id(self):
        """ Verify a list end point of program credentials will work with
        program_uuid filter.
        """
        error_message = {'error': 'A UUID query string parameter is required for filtering program credentials.'}
        self.assert_list_without_id_filter(path=self.list_path,
                                           data={'program_id': self.program_id},
                                           expected=error_message)

    def test_list_with_uuid_and_id(self):
        """ Verify a list end point of program credentials will not work with
        program_id filter.
        """
        error_message = {'error': 'A program_id query string parameter was found in a V2 API request.'}
        self.assert_list_without_id_filter(path=self.list_path,
                                           data={'program_uuid': self.program_uuid, 'program_id': self.program_id},
                                           expected=error_message)

    def test_list_with_program_uuid_filter(self):
        """ Verify the list endpoint supports filter data by program_uuid."""
        self.assert_list_with_id_filter(data={'program_uuid': self.program_uuid})

    def test_list_with_invalid_uuid(self):
        """ Verify the list endpoint will fail if given a bad uuid."""
        self.program_uuid = '12345678=0DAC-CAD0-ABCD-fedcba987654'
        self.assert_list_with_id_filter(data={'program_uuid': self.program_uuid}, should_exist=False)

    def test_list_with_status_filter(self):
        """ Verify the list endpoint supports filtering by status."""
        factories.UserCredentialFactory.create_batch(2, status=UserCredential.REVOKED,
                                                     username=self.user_credential.username)
        self.assert_list_with_status_filter(data={'program_uuid': self.program_uuid, 'status': UserCredential.AWARDED})

    def test_list_with_bad_status_filter(self):
        """ Verify the list endpoint supports filtering by status when there isn't anything available."""
        self.assert_list_with_status_filter(data={'program_uuid': self.program_uuid, 'status': UserCredential.REVOKED},
                                            should_exist=False)

    def test_permission_required(self):
        """ Verify that requests require explicit model permissions. """
        self.assert_permission_required({'program_uuid': self.program_uuid, 'status': UserCredential.AWARDED})


class UserCredentialViewSetTests(BaseUserCredentialViewSetTests, APITestCase):
    list_path = reverse("api:v2:usercredential-list")


class UserCredentialViewSetPermissionsTests(BaseUserCredentialViewSetPermissionsTests, APITestCase):
    list_path = reverse("api:v2:usercredential-list")


class CourseCredentialViewSetTests(BaseCourseCredentialViewSetTests, CredentialViewSetTestsMixin, APITestCase):
    list_path = reverse("api:v2:coursecredential-list")
