"""Creates or updates a Site including SiteConfiguration data."""

import logging

from django.contrib.sites.models import Site
from django.core.management import BaseCommand, CommandError

from credentials.apps.core.models import SiteConfiguration


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create or update Site and SiteConfiguration"

    def add_arguments(self, parser):
        parser.add_argument("--site-id", action="store", dest="site_id", type=int, help="ID of the Site to update.")
        parser.add_argument(
            "--site-domain",
            action="store",
            dest="site_domain",
            type=str,
            required=True,
            help="Domain of the Site to create or update.",
        )
        parser.add_argument(
            "--site-name",
            action="store",
            dest="site_name",
            type=str,
            required=True,
            help="Name of the Site to create or update.",
        )
        parser.add_argument(
            "--platform-name",
            action="store",
            dest="platform_name",
            type=str,
            required=True,
            help="Name of your Open edX platform.",
        )
        parser.add_argument(
            "--lms-url-root",
            action="store",
            dest="lms_url_root",
            type=str,
            required=True,
            help="Root URL of LMS (e.g. https://localhost:8000)",
        )
        parser.add_argument(
            "--catalog-api-url",
            action="store",
            dest="catalog_api_url",
            type=str,
            required=True,
            help="Root URL of the Catalog API (e.g. https://api.edx.org/catalog/v1/)",
        )
        parser.add_argument(
            "--tos-url", action="store", dest="tos_url", type=str, required=True, help="Terms of Service URL"
        )
        parser.add_argument(
            "--privacy-policy-url",
            action="store",
            dest="privacy_policy_url",
            type=str,
            required=True,
            help="Privacy Policy URL",
        )
        parser.add_argument(
            "--homepage-url", action="store", dest="homepage_url", type=str, required=True, help="Homepage URL"
        )
        parser.add_argument(
            "--company-name", action="store", dest="company_name", type=str, required=True, help="Company Name"
        )
        parser.add_argument(
            "--certificate-help-url",
            action="store",
            dest="certificate_help_url",
            type=str,
            required=True,
            help="Certificate Help URL",
        )
        parser.add_argument(
            "--records-help-url",
            action="store",
            dest="records_help_url",
            type=str,
            required=False,
            default="",
            help="Records Help URL",
        )
        parser.add_argument(
            "--segment-key", action="store", dest="segment_key", type=str, required=False, help="Segment API/write key"
        )
        parser.add_argument(
            "--twitter-username",
            action="store",
            dest="twitter_username",
            type=str,
            required=False,
            help="Twitter username attached to tweets",
        )
        parser.add_argument(
            "--facebook-app-id",
            action="store",
            dest="facebook_app_id",
            type=str,
            required=False,
            help="Facebook app ID associated with posts",
        )
        parser.add_argument(
            "--enable-facebook-sharing",
            action="store_true",
            dest="enable_facebook_sharing",
            required=False,
            help="Enable Facebook Sharing",
        )
        parser.add_argument(
            "--enable-linkedin-sharing",
            action="store_true",
            dest="enable_linkedin_sharing",
            required=False,
            help="Enable LinkedIn Sharing",
        )
        parser.add_argument(
            "--enable-twitter-sharing",
            action="store_true",
            dest="enable_twitter_sharing",
            required=False,
            help="Enable Twitter Sharing",
        )
        parser.add_argument(
            "--theme-name",
            action="store",
            dest="theme_name",
            type=str,
            required=False,
            help="Name of of the theme to use for this site. This value should be lower-cased.",
        )

    def handle(self, *args, **options):
        site_id = options.get("site_id")
        site_domain = options.get("site_domain")
        site_name = options.get("site_name")

        enable_facebook_sharing = options.get("enable_facebook_sharing")
        facebook_app_id = options.get("facebook_app_id")
        if enable_facebook_sharing and not facebook_app_id:
            raise CommandError("A Facebook app ID must be supplied to enable Facebook sharing")

        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            site, site_created = Site.objects.get_or_create(domain=site_domain)
            if site_created:
                logger.info("Created Site [%d] with domain [%s]", site.id, site.domain)

        site.domain = site_domain
        site.name = site_name
        site.save()

        SiteConfiguration.objects.update_or_create(
            site=site,
            defaults={
                "platform_name": options.get("platform_name"),
                "lms_url_root": options.get("lms_url_root"),
                "catalog_api_url": options.get("catalog_api_url"),
                "tos_url": options.get("tos_url"),
                "privacy_policy_url": options.get("privacy_policy_url"),
                "homepage_url": options.get("homepage_url"),
                "company_name": options.get("company_name"),
                "certificate_help_url": options.get("certificate_help_url"),
                "records_help_url": options.get("records_help_url"),
                "twitter_username": options.get("twitter_username"),
                "enable_linkedin_sharing": options.get("enable_linkedin_sharing"),
                "enable_twitter_sharing": options.get("enable_twitter_sharing"),
                "enable_facebook_sharing": enable_facebook_sharing,
                "facebook_app_id": facebook_app_id,
                "segment_key": options.get("segment_key"),
                "theme_name": options.get("theme_name").lower(),
            },
        )
