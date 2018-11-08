"""
Tests for credentials rendering views.
"""
import uuid

import ddt
import responses
from django.template import Context, Template
from django.template.loader import select_template
from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify
from faker import Faker
from mock import patch

from credentials.apps.core.tests.factories import USER_PASSWORD, SiteConfigurationFactory, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import ProgramCertificate, UserCredential
from credentials.apps.credentials.templatetags import i18n_assets
from credentials.apps.credentials.tests import factories


@ddt.ddt
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
        self.user_credential = factories.UserCredentialFactory(
            username=self.MOCK_USER_DATA['username'], credential=self.program_certificate
        )
        self.visible_date_attr = factories.UserCredentialAttributeFactory(
            user_credential=self.user_credential,
            name='visible_date',
            value='1970-01-01T01:01:01Z',
        )
        self.platform_name = self.site.siteconfiguration.platform_name
        user = UserFactory(username=self.MOCK_USER_DATA['username'])
        self.client.login(username=user.username, password=USER_PASSWORD)

    def _render_user_credential(self, use_proper_logo_url=True, user_credential=None, program_certificate=None):
        """ Helper method to render a user certificate."""
        user_credential = user_credential or self.user_credential
        program_certificate = program_certificate or self.program_certificate
        if use_proper_logo_url:
            certificate_logo_image_url = self.faker.url()
        else:
            certificate_logo_image_url = None
        program_uuid = program_certificate.program_uuid
        program_endpoint = 'programs/{uuid}/'.format(uuid=str(program_uuid))
        body = {
            'uuid': str(program_uuid),
            'title': self.PROGRAM_NAME,
            'subtitle': self.faker.word(),
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
            response = self.client.get(user_credential.get_absolute_url())
            self.assertEqual(response.status_code, 200)

        return response

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    @responses.activate
    def test_sharing_bar_with_anonymous_user(self):
        """ Verify that the view renders certificate without sharing bar. """
        self.client.logout()
        response = self._render_user_credential()

        self.assertNotContains(response, 'Print or share your certificate')

    @responses.activate
    def test_sharing_bar_with_staff_user(self):
        """ Verify that the view renders certificate with sharing bar. """
        self.client.logout()
        staff_user = UserFactory(is_staff=True)
        self.client.login(username=staff_user.username, password=USER_PASSWORD)
        response = self._render_user_credential()

        self.assertContains(response, 'Print or share your certificate')

    @responses.activate
    def test_awarded_with_logged_in_user(self):
        """ Verify that the view renders awarded certificates with sharing bar. """
        response = self._render_user_credential()
        response_context_data = response.context_data

        self.assertContains(response, 'Print or share your certificate')

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

    @responses.activate
    def test_invalid_site(self):
        """ Verify that the view returns a 404 if user_credentials are displayed on a site
        they are not associated with.
        """
        domain = 'unused.testsite'
        site_configuration = SiteConfigurationFactory(
            site__domain=domain,
        )
        test_site = site_configuration.site
        test_program_certificate = factories.ProgramCertificateFactory(site=test_site)
        test_signatory_1 = factories.SignatoryFactory()
        test_signatory_2 = factories.SignatoryFactory()
        test_program_certificate.signatories.add(test_signatory_1, test_signatory_2)
        test_user_credential = factories.UserCredentialFactory(
            username=self.MOCK_USER_DATA['username'], credential=test_program_certificate
        )
        response = self.client.get(test_user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        # Change the program certificate site to the client's site and check that the
        # response returns the user's certificate.
        test_program_certificate.site = self.site
        test_program_certificate.save()
        response = self._render_user_credential(user_credential=test_user_credential,
                                                program_certificate=test_program_certificate)
        self.assertEqual(response.status_code, 200)

    def test_invalid_credential(self):
        """ Verify the view returns 404 for attempts to render unsupported credentials. """
        self.user_credential = factories.UserCredentialFactory(credential=factories.CourseCertificateFactory())
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_future_visible_date(self):
        """ Verify that the view returns 404 when the uuid is valid but certificate is not yet visible. """
        self.visible_date_attr.value = '9999-01-01T01:01:01Z'
        self.visible_date_attr.save()
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    @responses.activate
    def test_invalid_visible_date(self):
        """ Verify that the view just returns normally when the valid_date attribute can't be understood. """
        self.visible_date_attr.value = 'hello'
        self.visible_date_attr.save()
        self._render_user_credential()  # Will raise exception if not 200 status

    @responses.activate
    def test_no_visible_date(self):
        """ Verify that the view just returns normally when there isn't a valid_date attribute. """
        self.visible_date_attr.delete()
        self._render_user_credential()  # Will raise exception if not 200 status

    @responses.activate
    def test_visible_date_as_issue_date(self):
        """ Verify that the view renders the visible_date as the issue date. """
        response = self._render_user_credential()
        self.assertContains(response, 'Issued January 1970')

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

    @ddt.data(
        (True, 'lang="es-419"'),
        (False, 'lang="en"')
    )
    @ddt.unpack
    @responses.activate
    def test_render_language(self, langauge_set, expected_text):
        """
        Verify that the view renders certificates in the configured language when it has been set,
        and in the default language (English) when content_language has not been set.
        """
        if langauge_set:
            ProgramCertificate.objects.update_or_create(program_uuid=self.program_certificate.program_uuid, defaults={
                'language': 'es_419'
            })
        response = self._render_user_credential()
        self.assertContains(response, expected_text)


@ddt.ddt
class ExampleCredentialTests(SiteMixin, TestCase):
    def test_get(self):
        """ Verify the view renders a credential. """
        response = self.client.get(reverse('credentials:example'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get('{}?program_type=professional-certificate'.format(reverse('credentials:example')))
        self.assertEqual(response.status_code, 200)


class I18nAssetsTemplateTagTest(TestCase):
    def test_construct_file_language_names(self):
        """ Verify that the method for constructing file paths properly creates the set"""
        filepath = 'some/test/path.svg'

        # Verify that for two different, full language codes all paths are generated, including the 2 characters ones
        language = 'es-419'
        default = 'en-US'
        paths = i18n_assets.construct_file_language_names(filepath, language, default)
        self.assertEqual(paths, [
            'some/test/path-es-419.svg',
            'some/test/path-es.svg',
            'some/test/path-en-US.svg',
            'some/test/path-en.svg',
            'some/test/path.svg',
        ])

        # Verify that for two identical, 2 character language codes, only that path and the default is generated
        language = 'en'
        default = 'en'
        paths = i18n_assets.construct_file_language_names(filepath, language, default)
        self.assertEqual(paths, [
            'some/test/path-en.svg',
            'some/test/path.svg',
        ])

    def test_translate_file_path_filter(self):
        """Verify that the filter correctly filters an image"""

        context = Context({})
        template_to_render = Template(
            '{% load i18n_assets %}'
            '{{ "openedx/images/example-logo.svg" | translate_file_path}}'
        )
        rendered_template = template_to_render.render(context)
        # Make sure the translated string occurs in the template
        self.assertEqual(rendered_template.find('openedx/images/example-logo-en.svg'), 0)
