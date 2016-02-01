""" Core context processors. """
from django.conf import settings


def core(request):
    """ Site-wide context processor. """
    return {
        'site': request.site,
        'platform_name': settings.PLATFORM_NAME,
        'language_code': request.LANGUAGE_CODE,
    }
