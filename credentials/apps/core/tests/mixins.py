from __future__ import unicode_literals

import json

import responses
from django.conf import settings
from django.contrib.sites.models import Site

from credentials.apps.core.tests.factories import SiteConfigurationFactory

JSON = 'application/json'


class SiteMixin(object):
    def setUp(self):
        super(SiteMixin, self).setUp()

        # Set the domain used for all test requests
        domain = 'testserver.fake'
        self.client = self.client_class(SERVER_NAME=domain)

        Site.objects.all().delete()  # pylint: disable=no-member
        site_configuration = SiteConfigurationFactory(
            site__domain=domain,
            site__id=settings.SITE_ID
        )
        self.site = site_configuration.site

    def mock_access_token_response(self, status=200):
        """ Mock the response from the OAuth provider's access token endpoint. """
        oauth2_provider_url = self.site.siteconfiguration.oauth2_provider_url  # pylint: disable=no-member
        url = '{root}/access_token'.format(root=oauth2_provider_url)
        token = 'abc123'
        body = json.dumps({
            'access_token': token,
            'expires_in': 3600,
        })
        responses.add(responses.POST, url, body=body, content_type=JSON, status=status)

        return token

    def mock_catalog_api_response(self, endpoint, body, status=200):
        """ Mock a response from a Catalog API endpoint. """
        endpoint = endpoint.strip('/')
        root = self.site.siteconfiguration.catalog_api_url.strip('/')  # pylint: disable=no-member
        url = '{root}/{endpoint}/'.format(root=root, endpoint=endpoint)
        responses.add(responses.GET, url, body=json.dumps(body), content_type=JSON, status=status)
