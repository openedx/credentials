""" Tests for core models. """
import json
import uuid
from unittest import mock

import responses
from django.contrib.sites.models import SiteManager
from django.test import TestCase, override_settings
from faker import Faker
from social_django.models import UserSocialAuth

from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.core.tests.mixins import JSON, SiteMixin


class UserTests(TestCase):
    """ User model tests. """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_access_token_without_social_auth(self):
        """ Verify the property returns None if the user is not associated with a UserSocialAuth. """
        self.assertIsNone(self.user.access_token)

    def test_access_token(self):
        """ Verify the property returns the value of the access_token stored with the UserSocialAuth. """
        social_auth = UserSocialAuth.objects.create(user=self.user, provider='test', uid=self.user.username)
        self.assertIsNone(self.user.access_token)

        access_token = 'My voice is my passport. Verify me.'
        social_auth.extra_data.update({'access_token': access_token})
        social_auth.save()
        self.assertEqual(self.user.access_token, access_token)

    def test_get_full_name(self):
        """ Test that the user model concatenates first and last name if the full name is not set. """
        full_name = "George Costanza"
        user = UserFactory(full_name=full_name)
        self.assertEqual(user.get_full_name(), full_name)

        first_name = "Jerry"
        last_name = "Seinfeld"
        user = UserFactory(full_name=None, first_name=first_name, last_name=last_name)
        expected = f"{first_name} {last_name}"
        self.assertEqual(user.get_full_name(), expected)

        user = UserFactory(full_name=full_name, first_name=first_name, last_name=last_name)
        self.assertEqual(user.get_full_name(), full_name)


class SiteConfigurationTests(SiteMixin, TestCase):
    """ Site configuration model tests. """

    def test_str(self):
        """ Test the site value for site configuration model. """
        site = SiteFactory(domain='test.org', name='test')
        site_configuration = SiteConfigurationFactory(site=site)
        self.assertEqual(str(site_configuration), site.name)

    @responses.activate
    def test_access_token(self):
        """ Verify the property retrieves, and caches, an access token from the OAuth 2.0 provider. """
        token = self.mock_access_token_response()
        self.assertEqual(self.site_configuration.access_token, token)
        self.assertEqual(len(responses.calls), 1)

        # Verify the value is cached
        self.assertEqual(self.site_configuration.access_token, token)
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_get_program(self):
        """ Verify the method retrieves program data from the Catalog API. """
        program_uuid = uuid.uuid4()
        program_endpoint = f'programs/{program_uuid}/'
        body = {
            'uuid': program_uuid.hex,
            'title': 'A Fake Program',
            'type': 'fake',
            'authoring_organizations': [
                {
                    'uuid': uuid.uuid4().hex,
                    'key': 'FakeX',
                    'name': 'Fake University',
                    'logo_image_url': 'https://static.fake.edu/logo.png',

                }
            ],
            'courses': []
        }

        self.mock_access_token_response()
        self.mock_catalog_api_response(program_endpoint, body)
        self.assertEqual(self.site_configuration.get_program(program_uuid), body)
        self.assertEqual(len(responses.calls), 2)

        # Verify the data is cached
        responses.reset()
        self.assertEqual(self.site_configuration.get_program(program_uuid), body)
        self.assertEqual(self.site_configuration.get_program(program_uuid), body)
        self.assertEqual(len(responses.calls), 0)

        # Verify the cache can be bypassed
        self.mock_access_token_response()
        self.mock_catalog_api_response(program_endpoint, body)
        self.assertEqual(self.site_configuration.get_program(program_uuid, ignore_cache=True), body)
        self.assertEqual(len(responses.calls), 1)

    def test_clear_site_cache_on_db_write(self):
        """ Verify the site cache is cleared whenever a SiteConfiguration instance is
        saved or deleted from the database. """
        with mock.patch.object(SiteManager, 'clear_cache') as mock_clear_site_cache:
            sc = SiteConfigurationFactory()
            mock_clear_site_cache.assert_called_once()

            mock_clear_site_cache.reset_mock()
            sc.delete()
            mock_clear_site_cache.assert_called_once()

    def test_user_api_url(self):
        """ Verify the User API URL is composed correctly. """
        expected = '{}/api/user/v1/'.format(self.site_configuration.lms_url_root.strip('/'))
        self.assertEqual(self.site_configuration.user_api_url, expected)

    @responses.activate
    @override_settings(USER_CACHE_TTL=60)
    def test_get_user_api_data(self):
        """ Verify the method retrieves data from the User API and caches it. """
        username = Faker().user_name()
        data = {
            'username': username,
        }
        url = f'{self.site_configuration.user_api_url}accounts/{username}'
        responses.add(responses.GET, url, body=json.dumps(data), content_type=JSON, status=200)
        self.mock_access_token_response()

        actual = self.site_configuration.get_user_api_data(username)
        self.assertEqual(actual, data)
        self.assertEqual(len(responses.calls), 2)

        # Verify the data is cached
        responses.reset()
        actual = self.site_configuration.get_user_api_data(username)
        self.assertEqual(actual, data)
        self.assertEqual(len(responses.calls), 0)
