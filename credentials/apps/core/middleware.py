from django.conf import settings
from django.contrib.sites.middleware import CurrentSiteMiddleware as DjangoCurrentSiteMiddleware


class CurrentSiteMiddleware(DjangoCurrentSiteMiddleware):
    """ This middleware behaves the same as the default CurrentSiteMiddleware,
    except certain paths can be exempted from the site requirement. This is useful
    for health checks on load balancers which might have numerous dynamic hostnames.
    We can avoid the hassle of having to update configuration for every new deployment.
    """

    def process_request(self, request):
        if request.path not in settings.CURRENT_SITE_MIDDLEWARE_EXEMPTED_PATHS:
            super().process_request(request)
