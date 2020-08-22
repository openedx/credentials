from urllib.parse import urljoin

from django.views.generic.base import RedirectView


class FaviconView(RedirectView):
    """
    Redirects to the favicon from the LMS
    """

    def get_redirect_url(self, *_args, **_kwargs):
        site_configuration = self.request.site.siteconfiguration
        if not site_configuration.homepage_url:
            return None
        return urljoin(site_configuration.homepage_url, "/favicon.ico")
