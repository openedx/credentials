""" Core context processors. """
from django.conf import settings
from django.contrib.sites.models import Site


def core(request):
    """ Site-wide context processor. """
    return {
        'site': Site.objects.get_current(),
        'platform_name': settings.PLATFORM_NAME,
        'language_code': request.LANGUAGE_CODE,
    }
