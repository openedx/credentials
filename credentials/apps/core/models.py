""" Core models. """

import datetime
import hashlib

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from edx_rest_api_client.client import EdxRestApiClient


class SiteConfiguration(models.Model):
    """
    SiteConfiguration model.

    .. no_pii: This model has no PII.
    """
    site = models.OneToOneField(Site, null=False, blank=False, on_delete=models.CASCADE)
    platform_name = models.CharField(
        verbose_name=_('Platform Name'),
        help_text=_('Name of your Open edX platform'),
        max_length=255,
        null=True,
        blank=False,
    )
    segment_key = models.CharField(
        verbose_name=_('Segment Key'),
        help_text=_('Segment write/API key.'),
        max_length=255,
        null=True,
        blank=True
    )
    theme_name = models.CharField(
        verbose_name=_('Theme Name'),
        help_text=_('Name of of the theme to use for this site. This value should be lower-cased.'),
        max_length=255,
        blank=False,
        default='openedx'
    )
    partner_from_address = models.EmailField(
        verbose_name='Email address for partners',
        help_text='An address to use for the "From" field of any automated emails sent out to partners. '
                  + 'If not defined, no-reply@sitedomain will be used.',
        blank=True,
        null=True,
    )
    lms_url_root = models.URLField(
        verbose_name=_('LMS base url for custom site'),
        help_text=_("Root URL of this site's LMS (e.g. https://courses.stage.edx.org)"),
        null=False,
        blank=False
    )
    catalog_api_url = models.URLField(
        verbose_name=_('Catalog API URL'),
        help_text=_('Root URL of the Catalog API (e.g. https://api.edx.org/catalog/v1/)'),
        blank=False,
        null=False
    )
    tos_url = models.URLField(
        verbose_name=_('Terms of Service URL'),
        blank=False,
        null=True,
    )
    privacy_policy_url = models.URLField(
        verbose_name=_('Privacy Policy URL'),
        blank=False,
        null=True,
    )
    homepage_url = models.URLField(
        verbose_name=_('Homepage URL'),
        blank=False,
        null=True,
    )
    company_name = models.CharField(
        verbose_name=_('Company Name'),
        max_length=255,
        blank=False,
        null=True,
    )
    verified_certificate_url = models.URLField(
        verbose_name=_('Verified Certificate URL'),
        help_text='This field is deprecated, and will be removed.',
        blank=True,
        null=True,
    )
    certificate_help_url = models.URLField(
        verbose_name=_('Certificate Help URL'),
        help_text=_('URL of page for questions about certificates'),
        blank=False,
        null=True,
    )
    records_enabled = models.BooleanField(
        verbose_name=_('Enable Learner Records'),
        help_text=_('Enable the Records feature. The LMS has a similar setting.'),
        default=True,
    )
    records_help_url = models.URLField(
        verbose_name=_('Learner Records Help URL'),
        help_text=_('URL of page for questions about Learner Records'),
        blank=True,
        null=False,
        default=''
    )
    facebook_app_id = models.CharField(
        verbose_name=_('Facebook App ID'),
        help_text=_('Facebook app ID used for sharing'),
        max_length=32,
        blank=True,
        null=True
    )
    twitter_username = models.CharField(
        verbose_name=_('Twitter Username'),
        help_text=_('Twitter username included in tweeted credentials. Do NOT include @.'),
        max_length=15,
        blank=True,
        null=True
    )
    enable_facebook_sharing = models.BooleanField(
        verbose_name=_('Enable Facebook sharing'),
        help_text=_('Enable sharing via Facebook'),
        default=False
    )
    enable_linkedin_sharing = models.BooleanField(
        verbose_name=_('Enable LinkedIn sharing'),
        help_text=_('Enable sharing via LinkedIn'),
        default=True
    )
    enable_twitter_sharing = models.BooleanField(
        verbose_name=_('Enable Twitter sharing'),
        help_text=_('Enable sharing via Twitter'),
        default=True
    )

    def __str__(self):
        return self.site.name

    @property
    def oauth2_provider_url(self):
        return settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL

    @property
    def oauth2_client_id(self):
        return settings.BACKEND_SERVICE_EDX_OAUTH2_KEY

    @property
    def oauth2_client_secret(self):
        return settings.BACKEND_SERVICE_EDX_OAUTH2_SECRET

    @property
    def user_api_url(self):
        return '{}/api/user/v1/'.format(self.lms_url_root.strip('/'))

    @property
    def access_token(self):
        """ Returns an access token for this site's service user.

        The access token is retrieved using the current site's OAuth credentials and the client credentials grant.
        The token is cached for the lifetime of the token, as specified by the OAuth provider's response. The token
        type is JWT.

        Returns:
            str: JWT access token
        """
        key = f'siteconfiguration_access_token_{self.id}'
        access_token = cache.get(key)

        if not access_token:
            url = f'{self.oauth2_provider_url}/access_token'
            access_token, expiration_datetime = EdxRestApiClient.get_oauth_access_token(
                url,
                self.oauth2_client_id,
                self.oauth2_client_secret,
                token_type='jwt'
            )

            expires = (expiration_datetime - datetime.datetime.utcnow()).seconds
            cache.set(key, access_token, expires)

        return access_token

    @cached_property
    def catalog_api_client(self):
        """
        Returns an API client for the Catalog API.

        Returns:
            EdxRestApiClient
        """

        return EdxRestApiClient(self.catalog_api_url, jwt=self.access_token)

    @cached_property
    def user_api_client(self):
        """
        Returns an authenticated User API client.

        Returns:
            EdxRestApiClient
        """

        return EdxRestApiClient(self.user_api_url, jwt=self.access_token, append_slash=False)

    def get_program(self, program_uuid, ignore_cache=False):
        """
        Retrieves the details for the specified program.

         Args:
             program_uuid (UUID): Program identifier
             ignore_cache (bool): Indicates if previously-cached data should be ignored.

         Returns:
             dict
        """
        program_uuid = str(program_uuid)
        cache_key = f'programs.api.data.{program_uuid}'

        if not ignore_cache:
            program = cache.get(cache_key)

            if program:
                return program

        program = self.catalog_api_client.programs(program_uuid).get()
        cache.set(cache_key, program, settings.PROGRAMS_CACHE_TTL)

        return program

    def get_user_api_data(self, username):
        """ Retrieve details for the specified user from the User API.

        If the API call is successful, the returned data will be cached for the
        duration of USER_CACHE_TTL (in seconds). Failed API responses will NOT
        be cached.

        Arguments:
            username (str): Unique identifier of the user for retrieval

        Returns:
            dict: Data returned from the User API
        """
        cache_key = 'user.api.data.{}'.format(hashlib.md5(username.encode('utf8')).hexdigest())
        user_data = cache.get(cache_key)

        if not user_data:
            user_data = self.user_api_client.accounts(username).get()
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
    full_name = models.CharField(_('Full Name'), max_length=255, blank=True, null=True)

    @property
    def access_token(self):
        """ Returns an OAuth2 access token for this user, if one exists; otherwise None.

        Assumes user has authenticated at least once with edX Open ID Connect.
        """
        try:
            return self.social_auth.first().extra_data['access_token']  # pylint: disable=no-member
        except Exception:  # pylint: disable=broad-except
            return None

    class Meta:
        get_latest_by = 'date_joined'

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.full_name or super().get_full_name()
