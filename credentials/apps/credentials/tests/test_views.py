"""
Tests for credentials rendering views.
"""
from __future__ import unicode_literals
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from credentials.apps.api.tests import factories
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests.mixins import OrganizationsDataMixin, ProgramsDataMixin
from credentials.apps.credentials.views import RenderCredential


class RenderCredentialPageTests(TestCase):
    """ Tests for credential rendering view. """

    def setUp(self):
        super(RenderCredentialPageTests, self).setUp()

        self.program_certificate = factories.ProgramCertificateFactory.create(template=None)
        self.user_credential = factories.UserCredentialFactory.create(
            credential=self.program_certificate
        )

    def _credential_url(self, uuid_string):
        """ Helper method to generate the url for a credential."""
        return reverse('credentials:render', kwargs={'uuid': uuid_string})

    def test_get_cert_with_awarded_status(self):
        """ Verify that the view renders a certificate and returns 200 when the
        uuid is valid and certificate status is 'awarded'.
        """
        path = self._credential_url(self.user_credential.uuid.hex)
        with patch('credentials.apps.credentials.views.get_program') as mock_program_data:
            mock_program_data.return_value = ProgramsDataMixin.PROGRAMS_API_RESPONSE
            with patch('credentials.apps.credentials.views.get_organization') as mock_org_data:
                mock_org_data.return_value = OrganizationsDataMixin.ORGANIZATIONS_API_RESPONSE
                response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
        self._assert_user_credential_template_data(response, self.user_credential)

    def test_get_cert_with_revoked_status(self):
        """ Verify that the view returns 404 when the uuid is valid but certificate status
        is 'revoked'.
        """
        self.user_credential.status = UserCredential.REVOKED
        self.user_credential.save()
        path = self._credential_url(self.user_credential.uuid.hex)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_get_cert_with_invalid_uuid(self):
        """ Verify that view returns 404 with invalid uuid."""
        path = self._credential_url(uuid.uuid4().hex)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_get_cert_with_wrong_certificate_type(self):
        """ Verify that the view returns 404 when the uuid refers to a certificate
        type other than a ProgramCertificate.
        """
        course_certificate = factories.CourseCertificateFactory.create(template=None)
        user_credential = factories.UserCredentialFactory.create(
            credential=course_certificate
        )

        path = self._credential_url(user_credential.uuid.hex)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def _assert_user_credential_template_data(self, response, user_credential):
        """ Verify the default template has the data. """
        self.assertContains(response, user_credential.username)
        self.assertContains(response, user_credential.uuid)

        issued_date = '{month} {day}, {year}'.format(
            month=user_credential.modified.strftime("%B"),
            day=user_credential.modified.day,
            year=user_credential.modified.year
        )
        self.assertContains(response, issued_date)
        self.assertContains(
            response,
            'XSeries Certificate | {platform_name}'.format(platform_name=settings.PLATFORM_NAME)
        )

        self.assertContains(response, 'organization-a')
        self.assertContains(response, 'xseries')
        self.assertContains(response, 2)

        self.assertContains(response, 'Test Organization')
        self.assertContains(response, 'test-org')
        self.assertContains(response, 'Organization for testing.')
        self.assertContains(response, 'http://testserver/media/organization_logos/test_org_logo.png')

    def test_get_programs_data(self):
        """ Verify the method parses the programs data correctly. """
        expected_data = {
            'course_count': 2,
            'organization_key': 'organization-a',
            'category': 'xseries'
        }

        with patch('credentials.apps.credentials.views.get_program') as mock_program_data:
            mock_program_data.return_value = ProgramsDataMixin.PROGRAMS_API_RESPONSE
            self.assertEqual(
                expected_data,
                RenderCredential()._get_program_data(100)  # pylint: disable=protected-access
            )
