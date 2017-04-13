from django.contrib.sites.models import Site
from django.test import RequestFactory, TestCase, override_settings

from credentials.apps.core.middleware import CurrentSiteMiddleware


class CurrentSiteMiddlewareTests(TestCase):
    @override_settings(SITE_ID=None)
    def test_process_request(self):
        """ The method should bypass setting request.site for exempted paths. """
        path = '/test/'
        request = RequestFactory().get(path)
        middleware = CurrentSiteMiddleware()

        # Rather than mock, we simply check for the expected error that occurs when
        # the SITE_ID is not set.
        with self.assertRaises(Site.DoesNotExist):
            middleware.process_request(request)

        with override_settings(CURRENT_SITE_MIDDLEWARE_EXEMPTED_PATHS=[path]):
            middleware.process_request(request)
            self.assertFalse(hasattr(request, 'site'))
