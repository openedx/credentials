"""
Tests for credentials rendering views.
"""
from __future__ import unicode_literals

import uuid

import ddt
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch
import responses

from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests import factories
from credentials.apps.credentials.tests.mixins import UserDataMixin


# pylint: disable=no-member
class RenderCredentialPageTests(SiteMixin, TestCase):
    """ Tests for credential rendering view. """
    PRIMARY_ORGANIZATION_KEY = 'ACMEx'
    PRIMARY_ORGANIZATION_CERTIFICATE_LOGO_URL = 'http://example.com/image.jpg'
    PRIMARY_ORGANIZATION_NAME = 'ACME University'

    def setUp(self):
        super(RenderCredentialPageTests, self).setUp()
        self.program_certificate = factories.ProgramCertificateFactory(site=self.site)
        self.signatory_1 = factories.SignatoryFactory()
        self.signatory_2 = factories.SignatoryFactory()
        self.program_certificate.signatories.add(self.signatory_1, self.signatory_2)
        self.user_credential = factories.UserCredentialFactory(credential=self.program_certificate)
        self.platform_name = self.site.siteconfiguration.platform_name

    def _render_user_credential(self, use_proper_logo_url=True):
        """ Helper method to render a user certificate."""
        if use_proper_logo_url:
            certificate_logo_image_url = self.PRIMARY_ORGANIZATION_CERTIFICATE_LOGO_URL
        else:
            certificate_logo_image_url = None
        program_uuid = self.program_certificate.program_uuid
        program_endpoint = 'programs/{uuid}/'.format(uuid=program_uuid.hex)
        body = {
            'uuid': program_uuid.hex,
            'title': 'Test Program',
            'type': 'XSeries',
            'authoring_organizations': [
                {
                    'uuid': uuid.uuid4().hex,
                    'key': self.PRIMARY_ORGANIZATION_KEY,
                    'name': self.PRIMARY_ORGANIZATION_NAME,
                    'certificate_logo_image_url': certificate_logo_image_url

                },
                {
                    'uuid': uuid.uuid4().hex,
                    'key': 'FakeX',
                    'name': 'Fake University',
                    'certificate_logo_image_url': 'http://example.com/image.jpg'
                }
            ],
            'courses': [
                {'key': 'ACMEx/101x'},
                {'key': 'FakeX/101x'},
            ]
        }
        self.mock_access_token_response()
        self.mock_catalog_api_response(program_endpoint, body)

        with patch('credentials.apps.credentials.views.get_user_data') as user_data:
            user_data.return_value = UserDataMixin.USER_API_RESPONSE
            response = self.client.get(self.user_credential.get_absolute_url())
            self.assertEqual(response.status_code, 200)

        return response

    @responses.activate
    def test_get_cert_with_awarded_status(self):
        """ Verify that the view renders awarded certificates. """
        response = self._render_user_credential()
        certificate_title = self.user_credential.credential.program_details.title
        self._assert_user_credential_template_data(response, self.user_credential, certificate_title=certificate_title)
        self._assert_signatory_data(response, self.signatory_1)
        self._assert_signatory_data(response, self.signatory_2)

    @responses.activate
    def test_get_cert_with_title_override(self):
        """ Verify that the view renders a valid certificate with the title
        value provided in its related certificate configuration.
        """
        # Add title value for the program certificate configuration
        certificate_title = 'Dummy title'
        self.program_certificate.title = certificate_title
        self.program_certificate.save()
        response = self._render_user_credential()

        self._assert_user_credential_template_data(response, self.user_credential, certificate_title=certificate_title)
        self._assert_signatory_data(response, self.signatory_1)
        self._assert_signatory_data(response, self.signatory_2)

    def test_get_cert_with_revoked_status(self):
        """ Verify that the view returns 404 when the uuid is valid but certificate status
        is 'revoked'.
        """
        self.user_credential.status = UserCredential.REVOKED
        self.user_credential.save()
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_get_cert_with_invalid_uuid(self):
        """ Verify that view returns 404 with invalid uuid."""
        path = reverse('credentials:render', kwargs={'uuid': uuid.uuid4().hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def _assert_user_credential_template_data(self, response, user_credential, certificate_title):
        """ Verify the default template has the data. """
        self.assertContains(response, 'Congratulations, Test User')
        self.assertContains(response, user_credential.uuid.hex)
        issued_date = '{month} {year}'.format(
            month=user_credential.modified.strftime("%B"),
            year=user_credential.modified.year
        )
        self.assertContains(response, issued_date)

        # test organization related data.
        self.assertContains(response, self.PRIMARY_ORGANIZATION_KEY)
        self.assertContains(response, self.PRIMARY_ORGANIZATION_CERTIFICATE_LOGO_URL)

        # test programs data
        self.assertContains(
            response,
            'a program offered by {org_name}, in collaboration with {platform_name}'.format(
                org_name=self.PRIMARY_ORGANIZATION_KEY,
                platform_name=self.platform_name
            )
        )
        self.assertContains(response, certificate_title)

        # test html strings are appearing on page.
        self.assertContains(
            response,
            'XSeries | {platform_name}'.format(platform_name=self.site.name)
        )
        self._assert_html_data(response)

    def _assert_html_data(self, response):
        """ Helper method to check html data."""
        self.assertContains(response, 'Print this certificate')
        # The title element of the svg logo
        self.assertContains(response, 'edx-logo-title')
        self.assertContains(response, 'images/edx-openedx-logo-tag.png')
        self.assertContains(response, 'offers interactive online classes and MOOCs from the')
        self.assertContains(
            response,
            'An {platform_name} XSeries Program certificate signifies that the learner has'.format(
                platform_name=self.platform_name
            )
        )
        self.assertContains(response, 'All rights reserved except where noted. edX')

    def _assert_signatory_data(self, response, signatory):
        """ DRY method to check signatory data."""
        self.assertContains(response, signatory.name)
        self.assertContains(response, signatory.title)
        self.assertContains(response, signatory.image)

    @responses.activate
    def test_signatory_organization_name_override(self):
        """ Verify that the view response contain signatory organization name
         if signatory have organization."""
        self.signatory_1.organization_name_override = 'edx'
        self.signatory_1.save()
        response = self._render_user_credential()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.signatory_1.organization_name_override)
        self.assertNotContains(response, self.signatory_2.organization_name_override)

    @responses.activate
    def test_logo_missing_exception(self):

        with self.assertRaisesRegexp(MissingCertificateLogoError, 'No certificate image logo defined for program'):
            self._render_user_credential(use_proper_logo_url=False)


@ddt.ddt
class ExampleCredentialTests(TestCase):
    def test_get(self):
        """ Verify the view works with no program_type parameter. """
        response = self.client.get(reverse('credentials:example'))
        self.assertEqual(response.status_code, 200)

    @ddt.data('micromasters', 'xseries', 'professional-certificate')
    def test_get_example_credentials(self, program_type):
        response = self.client.get('{}?program_type={}'.format(reverse('credentials:example'), program_type))
        self.assertEqual(response.status_code, 200)
        for asset in ('watermark', 'logo'):
            self.assertContains(response, '{}-{}'.format(program_type, asset))
