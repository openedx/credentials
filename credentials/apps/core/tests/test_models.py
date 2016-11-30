""" Tests for core models. """

import responses
from django.test import TestCase
from social.apps.django_app.default.models import UserSocialAuth

from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin


# pylint: disable=no-member
class UserTests(TestCase):
    """ User model tests. """

    def setUp(self):
        super(UserTests, self).setUp()
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
        expected = "{first_name} {last_name}".format(first_name=first_name, last_name=last_name)
        self.assertEqual(user.get_full_name(), expected)

        user = UserFactory(full_name=full_name, first_name=first_name, last_name=last_name)
        self.assertEqual(user.get_full_name(), full_name)


class SiteConfigurationTests(SiteMixin, TestCase):
    """ Site configuration model tests. """

    def test_unicode(self):
        """ Test the site value for site configuration model. """
        site = SiteFactory(domain='test.org', name='test')
        site_configuration = SiteConfigurationFactory(site=site)
        self.assertEqual(unicode(site_configuration), site.name)

    @responses.activate
    def test_access_token(self):
        """ Verify the property retrieves, and caches, an access token from the OAuth 2.0 provider. """
        token = self.mock_access_token_response()
        self.assertEqual(self.site.siteconfiguration.access_token, token)
        self.assertEqual(len(responses.calls), 1)

        # Verify the value is cached
        self.assertEqual(self.site.siteconfiguration.access_token, token)
        self.assertEqual(len(responses.calls), 1)
