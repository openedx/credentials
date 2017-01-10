""" Context processor tests. """

from django.test import RequestFactory, TestCase

from credentials.apps.core.context_processors import core
from credentials.apps.core.tests import factories

LANGUAGE_CODE = 'en'


class CoreContextProcessorTests(TestCase):
    """ Tests for core.context_processors.core """

    def test_core(self):
        site = factories.SiteFactory()
        request = RequestFactory().get('/')
        request.LANGUAGE_CODE = LANGUAGE_CODE
        request.site = site
        expected_output = {
            'site': site,
            'language_code': LANGUAGE_CODE,
        }
        self.assertDictEqual(core(request), expected_output)
