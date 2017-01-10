""" Core context processors. """


def core(request):
    """ Site-wide context processor. """
    return {
        'site': request.site,
        'language_code': request.LANGUAGE_CODE,
    }
