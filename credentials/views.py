from django.conf import settings
from django.views.generic.base import RedirectView


class FaviconView(RedirectView):
    """
    Redirects to the favicon from the LMS
    """

    def get_redirect_url(self, *_args, **_kwargs):
        if not settings.FAVICON_URL:
            return None
        return settings.FAVICON_URL
