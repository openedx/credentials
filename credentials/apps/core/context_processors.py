""" Core context processors. """


def core(request):
    """ Site-wide context processor. """
    site = request.site

    return {
        'site': site,
        'language_code': request.LANGUAGE_CODE,
        'platform_name': site.siteconfiguration.platform_name,
    }
