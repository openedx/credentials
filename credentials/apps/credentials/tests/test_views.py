"""
Tests for credentials rendering views.
"""
import uuid

import ddt
import responses
from django.template.loader import select_template
from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify
from faker import Faker
from mock import patch

from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import UserCredential
from credentials.apps.credentials.tests import factories


# pylint: disable=no-member
class RenderCredentialViewTests(SiteMixin, TestCase):
    faker = Faker()
    MOCK_USER_DATA = {'username': 'test-user', 'name': 'Test User', 'email': 'test@example.org', }
    PROGRAM_NAME = 'Fake PC'
    PROGRAM_TYPE = 'Professional Certificate'

    def setUp(self):
        super().setUp()
        self.program_certificate = factories.ProgramCertificateFactory(site=self.site)
        self.signatory_1 = factories.SignatoryFactory()
        self.signatory_2 = factories.SignatoryFactory()
        self.program_certificate.signatories.add(self.signatory_1, self.signatory_2)
        self.user_credential = factories.UserCredentialFactory(credential=self.program_certificate)
        self.platform_name = self.site.siteconfiguration.platform_name

    def _render_user_credential(self, use_proper_logo_url=True):
        """ Helper method to render a user certificate."""
        if use_proper_logo_url:
            certificate_logo_image_url = self.faker.url()
        else:
            certificate_logo_image_url = None
        program_uuid = self.program_certificate.program_uuid
        program_endpoint = 'programs/{uuid}/'.format(uuid=str(program_uuid))
        body = {
            'uuid': str(program_uuid),
            'title': self.PROGRAM_NAME,
            'type': self.PROGRAM_TYPE,
            'authoring_organizations': [
                {
                    'uuid': str(uuid.uuid4()),
                    'key': self.faker.word(),
                    'name': self.faker.word(),
                    'logo_image_url': self.faker.url(),
                    'certificate_logo_image_url': certificate_logo_image_url

                },
                {
                    'uuid': str(uuid.uuid4()),
                    'key': self.faker.word(),
                    'name': self.faker.word(),
                    'logo_image_url': self.faker.url(),
                    'certificate_logo_image_url': self.faker.url(),
                }
            ],
            'courses': [
                {'key': 'ACMEx/101x'},
                {'key': 'FakeX/101x'},
            ]
        }
        self.mock_access_token_response()
        self.mock_catalog_api_response(program_endpoint, body)

        with patch('credentials.apps.core.models.SiteConfiguration.get_user_api_data') as user_data:
            user_data.return_value = self.MOCK_USER_DATA
            response = self.client.get(self.user_credential.get_absolute_url())
            self.assertEqual(response.status_code, 200)

        return response

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    @responses.activate
    def test_awarded(self):
        """ Verify that the view renders awarded certificates. """
        response = self._render_user_credential()
        response_context_data = response.context_data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_context_data['user_credential'], self.user_credential)
        self.assertEqual(response_context_data['user_data'], self.MOCK_USER_DATA)
        self.assertEqual(response_context_data['page_title'], self.PROGRAM_TYPE)
        self.assertEqual(response_context_data['program_name'], self.PROGRAM_NAME)

        actual_child_templates = response_context_data['child_templates']
        expected_credential_template = 'openedx/credentials/programs/{}/certificate.html'.format(
            slugify(self.PROGRAM_TYPE))
        self.assert_matching_template_origin(actual_child_templates['credential'], expected_credential_template)
        self.assert_matching_template_origin(actual_child_templates['footer'], '_footer.html')
        self.assert_matching_template_origin(actual_child_templates['header'], '_header.html')

    def test_revoked(self):
        """ Verify that the view returns 404 when the uuid is valid but certificate status
        is 'revoked'.
        """
        self.user_credential.status = UserCredential.REVOKED
        self.user_credential.save()
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_invalid_uuid(self):
        """ Verify that view returns 404 with invalid uuid."""
        path = reverse('credentials:render', kwargs={'uuid': uuid.uuid4().hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_invalid_credential(self):
        """ Verify the view returns 404 for attempts to render unsupported credentials. """
        self.user_credential = factories.UserCredentialFactory(credential=factories.CourseCertificateFactory())
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    @responses.activate
    def test_signatory_organization_name_override(self):
        """ Verify that the view response contain signatory organization name if signatory have organization."""
        self.signatory_1.organization_name_override = self.faker.word()
        self.signatory_1.save()
        response = self._render_user_credential()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.signatory_1.organization_name_override)
        self.assertNotContains(response, self.signatory_2.organization_name_override)

    @responses.activate
    def test_logo_missing_exception(self):
        with self.assertRaisesMessage(MissingCertificateLogoError, 'No certificate image logo defined for program'):
            self._render_user_credential(use_proper_logo_url=False)


@ddt.ddt
class ExampleCredentialTests(SiteMixin, TestCase):
    def test_get(self):
        """ Verify the view renders a credential. """
        response = self.client.get(reverse('credentials:example'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get('{}?program_type=professional-certificate'.format(reverse('credentials:example')))
        self.assertEqual(response.status_code, 200)
