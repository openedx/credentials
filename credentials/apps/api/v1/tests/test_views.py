"""
Tests for credentials service views.
"""
# pylint: disable=no-member
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from credentials.apps.api.tests.mixins import CredentialViewSetTestsMixin
from credentials.apps.api.tests.test_views import (
    BaseUserCredentialViewSetTests, BaseUserCredentialViewSetPermissionsTests, BaseCourseCredentialViewSetTests,
)
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests import factories


class ProgramCredentialViewSetTests(CredentialViewSetTestsMixin, APITestCase):
    """ Tests for ProgramCredentialViewSetTests. """

    list_path = reverse("api:v1:programcredential-list")

    def setUp(self):
        super(ProgramCredentialViewSetTests, self).setUp()

        self.program_certificate = factories.ProgramCertificateFactory()
        self.program_id = self.program_certificate.program_id
        self.user_credential = factories.UserCredentialFactory.create(credential=self.program_certificate)
        self.request = APIRequestFactory().get('/')

    def test_list_without_program_id(self):
        """ Verify a list end point of program credentials will work only with
        program_id filter.
        """
        self.assert_list_without_id_filter(path=self.list_path, expected={
            'error': 'A program_id query string parameter is required for filtering program credentials.'
        })

    def test_list_with_program_id_filter(self):
        """ Verify the list endpoint supports filter data by program_id."""
        program_cert = factories.ProgramCertificateFactory(program_id=1)
        factories.UserCredentialFactory.create(credential=program_cert)
        self.assert_list_with_id_filter(data={'program_id': self.program_id})

    def test_list_with_program_invalid_id_filter(self):
        """ Verify the list endpoint supports filter data by program_id."""
        program_cert = factories.ProgramCertificateFactory(program_id=1)
        factories.UserCredentialFactory.create(credential=program_cert)
        self.assert_list_with_id_filter(data={'program_id': 50}, should_exist=False)

    def test_list_with_status_filter(self):
        """ Verify the list endpoint supports filtering by status."""
        factories.UserCredentialFactory.create_batch(2, status=UserCredential.REVOKED,
                                                     username=self.user_credential.username)
        self.assert_list_with_status_filter(data={'program_id': self.program_id, 'status': UserCredential.AWARDED})

    def test_list_with_bad_status_filter(self):
        """ Verify the list endpoint supports filtering by status."""
        self.assert_list_with_status_filter(data={'program_id': self.program_id, 'status': UserCredential.REVOKED},
                                            should_exist=False)

    def test_permission_required(self):
        """ Verify that requests require explicit model permissions. """
        self.assert_permission_required({'program_id': self.program_id, 'status': UserCredential.AWARDED})


class UserCredentialViewSetTests(BaseUserCredentialViewSetTests, APITestCase):
    list_path = reverse("api:v1:usercredential-list")


class UserCredentialViewSetPermissionsTests(BaseUserCredentialViewSetPermissionsTests, APITestCase):
    list_path = reverse("api:v1:usercredential-list")


class CourseCredentialViewSetTests(BaseCourseCredentialViewSetTests, CredentialViewSetTestsMixin, APITestCase):
    list_path = reverse("api:v1:coursecredential-list")
