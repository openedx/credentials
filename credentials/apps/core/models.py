"""Core models."""

import hashlib
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _
from edx_rest_api_client.client import OAuthAPIClient


class SiteConfiguration(models.Model):
    """
    SiteConfiguration model.

    .. no_pii: This model has no PII.
    """

    site = models.OneToOneField(Site, null=False, blank=False, on_delete=models.CASCADE)
    platform_name = models.CharField(
        verbose_name=_("Platform Name"),
        help_text=_("Name of your Open edX platform"),
        max_length=255,
        null=True,
        blank=False,
    )
    segment_key = models.CharField(
        verbose_name=_("Segment Key"), help_text=_("Segment write/API key."), max_length=255, null=True, blank=True
    )
    theme_name = models.CharField(
        verbose_name=_("Theme Name"),
        help_text=_("Name of of the theme to use for this site. This value should be lower-cased."),
        max_length=255,
        blank=False,
        default="openedx",
    )
    partner_from_address = models.EmailField(
        verbose_name="Email address for partners",
        help_text='An address to use for the "From" field of any automated emails sent out to partners. '
        + "If not defined, no-reply@sitedomain will be used.",
        blank=True,
        null=True,
    )
    lms_url_root = models.URLField(
        verbose_name=_("LMS base url for custom site"),
        help_text=_("Root URL of this site's LMS (e.g. https://courses.stage.edx.org)"),
        null=False,
        blank=False,
    )
    catalog_api_url = models.URLField(
        verbose_name=_("Catalog API URL"),
        help_text=_("Root URL of the Catalog API (e.g. https://api.edx.org/catalog/v1/)"),
        blank=False,
        null=False,
    )
    tos_url = models.URLField(
        verbose_name=_("Terms of Service URL"),
        blank=False,
        null=True,
    )
    privacy_policy_url = models.URLField(
        verbose_name=_("Privacy Policy URL"),
        blank=False,
        null=True,
    )
    homepage_url = models.URLField(
        verbose_name=_("Homepage URL"),
        blank=False,
        null=True,
    )
    company_name = models.CharField(
        verbose_name=_("Company Name"),
        max_length=255,
        blank=False,
        null=True,
    )
    verified_certificate_url = models.URLField(
        verbose_name=_("Verified Certificate URL"),
        help_text="This field is deprecated, and will be removed.",
        blank=True,
        null=True,
    )
    certificate_help_url = models.URLField(
        verbose_name=_("Certificate Help URL"),
        help_text=_("URL of page for questions about certificates"),
        blank=False,
        null=True,
    )
    records_enabled = models.BooleanField(
        verbose_name=_("Enable Learner Records"),
        help_text=_("Enable the Records feature. The LMS has a similar setting."),
        default=True,
    )
    records_help_url = models.URLField(
        verbose_name=_("Learner Records Help URL"),
        help_text=_("URL of page for questions about Learner Records"),
        blank=True,
        null=False,
        default="",
    )
    facebook_app_id = models.CharField(
        verbose_name=_("Facebook App ID"),
        help_text=_("Facebook app ID used for sharing"),
        max_length=32,
        blank=True,
        null=True,
    )
    twitter_username = models.CharField(
        verbose_name=_("Twitter Username"),
        help_text=_("Twitter username included in tweeted credentials. Do NOT include @."),
        max_length=15,
        blank=True,
        null=True,
    )
    enable_facebook_sharing = models.BooleanField(
        verbose_name=_("Enable Facebook sharing"), help_text=_("Enable sharing via Facebook"), default=False
    )
    enable_linkedin_sharing = models.BooleanField(
        verbose_name=_("Enable LinkedIn sharing"), help_text=_("Enable sharing via LinkedIn"), default=True
    )
    enable_twitter_sharing = models.BooleanField(
        verbose_name=_("Enable Twitter sharing"), help_text=_("Enable sharing via Twitter"), default=True
    )

    def __str__(self):
        return self.site.name

    @property
    def user_api_url(self):
        return "{}/api/user/v1/".format(self.lms_url_root.strip("/"))

    @property
    def name_verification_api_url(self):
        return "{}/api/edx_name_affirmation/v1/verified_name".format(self.lms_url_root.strip("/"))

    @property
    def api_client(self):
        """
        Returns a requests client for this site's service user.

        This client is authenticated with the configured oauth settings and automatically cached.

        Returns:
            requests.Session: API client
        """
        return OAuthAPIClient(
            settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL,
            settings.BACKEND_SERVICE_EDX_OAUTH2_KEY,
            settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET,
        )

    def get_user_api_data(self, username):
        """Retrieve details for the specified user from the User API and Verified Name API.

        If the API calls are successful, the returned data will be cached for the
        duration of USER_CACHE_TTL (in seconds). Failed API responses will NOT
        be cached.

        Arguments:
            username (str): Unique identifier of the user for retrieval

        Returns:
            dict: Data returned from the User API
        """
        cache_key = "user.api.data.{}".format(hashlib.md5(username.encode("utf8")).hexdigest())
        user_data = cache.get(cache_key)

        if not user_data:
            # first get user api data
            user_url = urljoin(self.user_api_url, f"accounts/{username}")
            user_response = self.api_client.get(user_url)
            user_response.raise_for_status()
            user_data = user_response.json()

            # then get name verification api data
            verification_url = urljoin(self.name_verification_api_url, f"?username={username}")
            verification_response = self.api_client.get(verification_url)
            if verification_response.status_code == 200:
                verification_data = verification_response.json()
                # add relevant verified name data to user_data
                user_data["verified_name"] = verification_data.get("verified_name")
                user_data["use_verified_name_for_certs"] = verification_data.get("use_verified_name_for_certs")

            cache.set(cache_key, user_data, settings.USER_CACHE_TTL)

        return user_data


class User(AbstractUser):
    """
    Custom user model for use with python-social-auth via edx-auth-backends.

    .. pii: Stores email, first name, full name, last name, and username for a user.
        pii values: email, first_name, full_name, last_name and username
    .. pii_types: email_address, name, username
    .. pii_retirement: retained
    """

    full_name = models.CharField(_("Full Name"), max_length=255, blank=True, null=True, db_index=True)
    lms_user_id = models.IntegerField(null=True, db_index=True)

    class Meta:
        get_latest_by = "date_joined"
        indexes = [
            models.Index(fields=["is_staff", "is_superuser", "is_active"]),
        ]

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.full_name or super().get_full_name()
