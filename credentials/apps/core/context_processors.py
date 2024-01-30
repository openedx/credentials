""" Core context processors. """

from django.conf import settings


def core(request):
    """Site-wide context processor."""
    site = request.site

    return {
        "site": site,
        "language_code": request.LANGUAGE_CODE,
        "platform_name": site.siteconfiguration.platform_name,
        "site_logo_url": getattr(settings, "LOGO_URL", ""),
        "openedx_logo_url": getattr(settings, "LOGO_POWERED_BY_OPEN_EDX_URL", ""),
        "favicon_url": getattr(settings, "FAVICON_URL", ""),
    }
