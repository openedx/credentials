""" Context processor tests. """

from django.test import RequestFactory, TestCase

from credentials.apps.core.context_processors import core
from credentials.apps.core.tests import factories


LANGUAGE_CODE = 'en'


class CoreContextProcessorTests(TestCase):
    """ Tests for core.context_processors.core """

    def test_core(self):
        site_configuration = factories.SiteConfigurationFactory()

        request = RequestFactory().get('/')
        request.LANGUAGE_CODE = LANGUAGE_CODE
        request.site = site_configuration.site

        expected_output = {
            'site': site_configuration.site,
            'language_code': LANGUAGE_CODE,
            'platform_name': site_configuration.platform_name
        }

        self.assertDictEqual(core(request), expected_output)
