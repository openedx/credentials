from django.conf import settings
from django.test import TestCase

from credentials.apps.badges.accredible.utils import get_accredible_api_base_url, get_accredible_base_url


class TestGetAccredibleBaseUrl(TestCase):
    def test_get_accredible_base_url_sandbox(self):
        settings.BADGES_CONFIG["accredible"] = {
            "ACCREDIBLE_BASE_URL": "https://accredible.com",
            "ACCREDIBLE_SANDBOX_BASE_URL": "https://sandbox.accredible.com",
            "ACCREDIBLE_SANDBOX_API_BASE_URL": "https://sandbox.api.accredible.com/v1/",
            "USE_SANDBOX": True,
        }

        result = get_accredible_base_url(settings)
        self.assertEqual(result, "https://sandbox.accredible.com")

    def test_get_accredible_base_url_production(self):
        settings.BADGES_CONFIG["accredible"] = {
            "ACCREDIBLE_BASE_URL": "https://accredible.com",
            "ACCREDIBLE_SANDBOX_BASE_URL": "https://sandbox.accredible.com",
            "ACCREDIBLE_SANDBOX_API_BASE_URL": "https://sandbox.api.accredible.com/v1/",
            "USE_SANDBOX": False,
        }
        result = get_accredible_base_url(settings)
        self.assertEqual(result, "https://accredible.com")


class TestGetAccredibleApiBaseUrl(TestCase):
    def test_get_accredible_api_base_url_sandbox(self):
        settings.BADGES_CONFIG["accredible"] = {
            "ACCREDIBLE_API_BASE_URL": "https://api.accredible.com/v1/",
            "ACCREDIBLE_SANDBOX_API_BASE_URL": "https://sandbox.api.accredible.com/v1/",
            "USE_SANDBOX": True,
        }
        result = get_accredible_api_base_url(settings)
        self.assertEqual(result, "https://sandbox.api.accredible.com/v1/")

    def test_get_accredible_api_base_url_production(self):
        settings.BADGES_CONFIG["accredible"] = {
            "ACCREDIBLE_API_BASE_URL": "https://api.accredible.com/v1/",
            "ACCREDIBLE_SANDBOX_API_BASE_URL": "https://sandbox.api.accredible.com/v1/",
            "USE_SANDBOX": False,
        }
        result = get_accredible_api_base_url(settings)
        self.assertEqual(result, "https://api.accredible.com/v1/")
