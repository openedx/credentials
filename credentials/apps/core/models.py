""" Core models. """

from __future__ import unicode_literals

import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from edx_rest_api_client.client import EdxRestApiClient


class SiteConfiguration(models.Model):
    site = models.OneToOneField(Site, null=False, blank=False)
    platform_name = models.CharField(
        verbose_name=_('Platform Name'),
        help_text=_('Name of your Open edX platform'),
        max_length=255,
        null=True,
        blank=False,
    )
    lms_url_root = models.URLField(
        verbose_name=_('LMS base url for custom site'),
        help_text=_("Root URL of this site's LMS (e.g. https://courses.stage.edx.org)"),
        null=True,
        blank=False
    )
    catalog_api_url = models.URLField(
        verbose_name=_('Catalog API URL'),
        help_text=_('Root URL of the Catalog API (e.g. https://api.edx.org/catalog/v1/)'),
        blank=False,
        null=True
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
        help_text=_('URL of page for information on verified certificates'),
        blank=False,
        null=True,
    )
    certificate_help_url = models.URLField(
        verbose_name=_('Certificate Help URL'),
        help_text=_('URL of page for questions about certificates'),
        blank=False,
        null=True,
    )

    def __unicode__(self):
        return unicode(self.site.name)

    @property
    def oauth2_provider_url(self):
        return settings.SOCIAL_AUTH_EDX_OIDC_URL_ROOT

    @property
    def oauth2_client_id(self):
        return settings.SOCIAL_AUTH_EDX_OIDC_KEY

    @property
    def oauth2_client_secret(self):
        return settings.SOCIAL_AUTH_EDX_OIDC_SECRET

    @property
    def access_token(self):
        """ Returns an access token for this site's service user.

        The access token is retrieved using the current site's OAuth credentials and the client credentials grant.
        The token is cached for the lifetime of the token, as specified by the OAuth provider's response. The token
        type is JWT.

        Returns:
            str: JWT access token
        """
        key = 'siteconfiguration_access_token_{}'.format(self.id)
        access_token = cache.get(key)

        if not access_token:
            url = '{root}/access_token'.format(root=self.oauth2_provider_url)
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


class User(AbstractUser):
    """ Custom user model for use with OpenID Connect. """
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

    class Meta(object):  # pylint:disable=missing-docstring
        get_latest_by = 'date_joined'

    def __unicode__(self):
        return unicode(self.full_name)

    def get_full_name(self):
        return self.full_name or super(User, self).get_full_name()
