import ddt
from django.contrib.sites.models import Site
from django.core.management import CommandError, call_command
from django.test import TestCase
from faker import Faker

from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory
from credentials.apps.core.tests.mixins import SiteMixin


@ddt.ddt
class CreateOrUpdateSiteCommandTests(SiteMixin, TestCase):
    COMMAND_NAME = 'create_or_update_site'
    faker = Faker()

    def setUp(self):
        super().setUp()
        self.site_configuration = SiteConfigurationFactory.build(segment_key=self.faker.word())

    def _call_command(self, site_domain, site_name, site_id=None, **kwargs):
        """
        Internal helper method for interacting with the create_or_update_site management command
        """
        default_kwargs = {
            'twitter_username': self.site_configuration.twitter_username,
            'segment_key': self.site_configuration.segment_key,
        }
        default_kwargs.update(kwargs)

        # Required arguments
        command_args = [
            f'--site-domain={site_domain}',
            f'--platform-name={self.site_configuration.platform_name}',
            f'--lms-url-root={self.site_configuration.lms_url_root}',
            f'--catalog-api-url={self.site_configuration.catalog_api_url}',
            f'--site-name={site_name}',
            f'--tos-url={self.site_configuration.tos_url}',
            '--privacy-policy-url={privacy_policy_url}'.format(
                privacy_policy_url=self.site_configuration.privacy_policy_url
            ),
            f'--homepage-url={self.site_configuration.homepage_url}',
            f'--company-name={self.site_configuration.company_name}',
            f'--certificate-help-url={self.site_configuration.certificate_help_url}',
            f'--records-help-url={self.site_configuration.records_help_url}',
            f'--theme-name={self.site_configuration.theme_name}',
        ]

        if site_id:
            command_args.append(f'--site-id={site_id}')

        call_command(self.COMMAND_NAME, *command_args, **default_kwargs)

    def _check_site_configuration(self, site_configuration):
        """
        Helper method for verifying that the Site is properly configured.

        Args:
            site_configuration (SiteConfiguration): SiteConfiguration that's being verified.
        """
        self.assertEqual(site_configuration.lms_url_root, self.site_configuration.lms_url_root)
        self.assertEqual(site_configuration.platform_name, self.site_configuration.platform_name)
        self.assertEqual(site_configuration.catalog_api_url, self.site_configuration.catalog_api_url)
        self.assertEqual(site_configuration.tos_url, self.site_configuration.tos_url)
        self.assertEqual(site_configuration.privacy_policy_url, self.site_configuration.privacy_policy_url)
        self.assertEqual(site_configuration.homepage_url, self.site_configuration.homepage_url)
        self.assertEqual(site_configuration.company_name, self.site_configuration.company_name)
        self.assertEqual(site_configuration.certificate_help_url, self.site_configuration.certificate_help_url)
        self.assertEqual(site_configuration.records_help_url, self.site_configuration.records_help_url)
        self.assertEqual(site_configuration.twitter_username, self.site_configuration.twitter_username)
        self.assertEqual(site_configuration.facebook_app_id, self.site_configuration.facebook_app_id)
        self.assertEqual(site_configuration.segment_key, self.site_configuration.segment_key)
        self.assertEqual(site_configuration.theme_name, self.site_configuration.theme_name)

        # Social sharing is disabled by default, if the flag is not passed
        self.assertFalse(site_configuration.enable_linkedin_sharing)
        self.assertFalse(site_configuration.enable_twitter_sharing)
        self.assertFalse(site_configuration.enable_facebook_sharing)

    def test_create_site(self):
        """ Verify the command creates Site and SiteConfiguration. """
        site_domain = self.faker.domain_name()

        self._call_command(
            site_domain=site_domain,
            site_name=self.site_configuration.site.name
        )

        site = Site.objects.get(domain=site_domain)
        self._check_site_configuration(site.siteconfiguration)

    def test_update_site(self):
        """ Verify the command updates Site and SiteConfiguration. """
        expected_site_domain = self.faker.domain_name()
        expected_site_name = 'Fake Credentials Server'
        site = SiteFactory()

        self._call_command(
            site_id=site.id,
            site_domain=expected_site_domain,
            site_name=expected_site_name
        )

        site.refresh_from_db()

        self.assertEqual(site.domain, expected_site_domain)
        self.assertEqual(site.name, expected_site_name)
        self._check_site_configuration(site.siteconfiguration)

    @ddt.data(
        ['--site-id=1'],
        ['--site-id=1', '--site-domain=fake.server'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'
         '--privacy-policy-url=fake.privacy.policy'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'
         '--privacy-policy-url=fake.privacy.policy', '--homepage-url=fake.home.page'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'
         '--privacy-policy-url=fake.privacy.policy', '--homepage-url=fake.home.page', '--company-name=Fake Company'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'
         '--privacy-policy-url=fake.privacy.policy', '--homepage-url=fake.home.page', '--company-name=Fake Company'
         '--verified-certificate-url=fake.verified.url'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'
         '--privacy-policy-url=fake.privacy.policy', '--homepage-url=fake.home.page', '--company-name=Fake Company'
         '--certificate-help-url==fake.certificate.url'],
        ['--site-id=1', '--site-domain=fake.server', '--platform-name=Fake Name', '--lms-url-root=fake.lms.server'
         '--catalog-api-url=fake.catalog.server', '--site-name=Fake Site Name', '--tos-url=fake.tos.url'
         '--privacy-policy-url=fake.privacy.policy', '--homepage-url=fake.home.page', '--company-name=Fake Company'
         '--certificate-help-url==fake.certificate.url', '--records-help-url=fake.records.url'],
    )
    def test_missing_arguments(self, command_args):
        """ Verify CommandError is raised when required arguments are missing """
        with self.assertRaises(CommandError):
            call_command(self.COMMAND_NAME, *command_args)

    @ddt.data('enable_linkedin_sharing', 'enable_twitter_sharing')
    def test_enable_social_sharing(self, flag_name):
        """ Verify the command supports activating social sharing functionality. """

        self._call_command(
            site_domain=self.site.domain,
            site_name=self.site.name,
            **{flag_name: True}
        )

        self.site.refresh_from_db()
        self.assertTrue(getattr(self.site.siteconfiguration, flag_name))

    def test_invalid_facebook_configuration(self):
        """ Verify the Facebook app ID is required to enable Facebook sharing. """
        kwargs = {'enable_facebook_sharing': True}

        with self.assertRaisesMessage(CommandError, 'A Facebook app ID must be supplied to enable Facebook sharing'):
            self._call_command(site_domain=self.site.domain, site_name=self.site.name, **kwargs)

        kwargs['facebook_app_id'] = self.faker.word()
        self._call_command(site_domain=self.site.domain, site_name=self.site.name, **kwargs)

        site_configuration = self.site.siteconfiguration
        site_configuration.refresh_from_db()
        self.assertTrue(site_configuration.enable_facebook_sharing)
        self.assertEqual(site_configuration.facebook_app_id, kwargs['facebook_app_id'])
