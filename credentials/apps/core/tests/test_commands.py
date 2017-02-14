from ddt import data, ddt

from django.contrib.sites.models import Site
from django.core.management import CommandError, call_command
from django.test import TestCase

from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory


@ddt
class CreateOrUpdateSiteCommandTests(TestCase):
    command_name = 'create_or_update_site'

    def setUp(self):
        super(CreateOrUpdateSiteCommandTests, self).setUp()

        self.site_configuration = SiteConfigurationFactory.build()

    def _call_command(self, site_domain, site_name, site_id=None):
        """
        Internal helper method for interacting with the create_or_update_site management command
        """
        # Required arguments
        command_args = [
            '--site-domain={site_domain}'.format(site_domain=site_domain),
            '--platform-name={platform_name}'.format(platform_name=self.site_configuration.platform_name),
            '--lms-url-root={lms_url_root}'.format(lms_url_root=self.site_configuration.lms_url_root),
            '--catalog-api-url={catalog_api_url}'.format(catalog_api_url=self.site_configuration.catalog_api_url),
            '--site-name={site_name}'.format(site_name=site_name),
            '--tos-url={tos_url}'.format(tos_url=self.site_configuration.tos_url),
            '--privacy-policy-url={privacy_policy_url}'.format(
                privacy_policy_url=self.site_configuration.privacy_policy_url
            ),
            '--homepage-url={homepage_url}'.format(homepage_url=self.site_configuration.homepage_url),
            '--company-name={company_name}'.format(company_name=self.site_configuration.company_name),
            '--verified-certificate-url={verified_certificate_url}'.format(
                verified_certificate_url=self.site_configuration.verified_certificate_url
            ),
            '--certificate-help-url={certificate_help_url}'.format(
                certificate_help_url=self.site_configuration.certificate_help_url
            )
        ]

        if site_id:
            command_args.append('--site-id={site_id}'.format(site_id=site_id))

        call_command(self.command_name, *command_args)

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
        self.assertEqual(site_configuration.verified_certificate_url, self.site_configuration.verified_certificate_url)
        self.assertEqual(site_configuration.certificate_help_url, self.site_configuration.certificate_help_url)

    def test_create_site(self):
        """ Verify the command creates Site and SiteConfiguration. """
        site_domain = 'credentials-fake1.server'

        self._call_command(
            site_domain=site_domain,
            site_name=self.site_configuration.site.name
        )

        site = Site.objects.get(domain=site_domain)
        self._check_site_configuration(site.siteconfiguration)

    def test_update_site(self):
        """ Verify the command updates Site and SiteConfiguration. """
        site_domain = 'credentials-fake2.server'
        updated_site_domain = 'credentials-fake3.server'
        updated_site_name = 'Fake Credentials Server'
        site = SiteFactory(domain=site_domain)

        self._call_command(
            site_id=site.id,
            site_domain=updated_site_domain,
            site_name=updated_site_name
        )

        site.refresh_from_db()

        self.assertEqual(site.domain, updated_site_domain)
        self.assertEqual(site.name, updated_site_name)
        self._check_site_configuration(site.siteconfiguration)

    @data(
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
    )
    def test_missing_arguments(self, command_args):
        """ Verify CommandError is raised when required arguments are missing """
        with self.assertRaises(CommandError):
            call_command(self.command_name, *command_args)
