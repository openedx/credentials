""" Context processor tests. """

from django.contrib.sites.models import Site
from django.test import override_settings, RequestFactory, TestCase

from credentials.apps.core.context_processors import core


LANGUAGE_CODE = 'en'
PLATFORM_NAME = 'Test Platform'


class CoreContextProcessorTests(TestCase):
    """ Tests for core.context_processors.core """

    @override_settings(PLATFORM_NAME=PLATFORM_NAME)
    def test_core(self):
        request = RequestFactory().get('/')
        request.LANGUAGE_CODE = LANGUAGE_CODE
        self.assertDictEqual(
            core(request),
            {'site': Site.objects.get_current(), 'platform_name': PLATFORM_NAME, 'language_code': LANGUAGE_CODE}
        )
