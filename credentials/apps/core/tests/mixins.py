import json

import responses
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from edx_django_utils.cache import TieredCache

from credentials.apps.core.tests.factories import SiteConfigurationFactory

JSON = "application/json"


class SiteMixin:
    def setUp(self):
        super().setUp()
        cache.clear()

        # Set the domain used for all test requests
        domain = "testserver.fake"
        self.client = self.client_class(SERVER_NAME=domain)

        Site.objects.all().delete()
        self.site_configuration = SiteConfigurationFactory(site__domain=domain, site__id=settings.SITE_ID)
        self.site = self.site_configuration.site

        # Clear edx rest api client cache
        TieredCache.dangerous_clear_all_tiers()

    def mock_access_token_response(self, status=200):
        """Mock the response from the OAuth provider's access token endpoint."""
        oauth2_provider_url = settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL
        url = f"{oauth2_provider_url}/access_token"
        token = "abc123"
        body = json.dumps(
            {
                "access_token": token,
                "expires_in": 3600,
            }
        )
        responses.add(responses.POST, url, body=body, content_type=JSON, status=status)

        return token

    def mock_catalog_api_response(self, endpoint, body, status=200):
        """Mock a response from a Catalog API endpoint."""
        root = self.site.siteconfiguration.catalog_api_url.strip("/")
        url = f"{root}/{endpoint}"
        responses.add(
            responses.GET, url, body=json.dumps(body), content_type=JSON, status=status, match_querystring=True
        )
