"""
Template tags for credentials.
"""
import urllib

from django import template


register = template.Library()


@register.filter(name='strip_querystrings')
def strip_querystrings(value):
    """ Helper method to remove querystrings from the provided url.

    If url has querystring params than split it and return the first part.

    Arguments:
        url (str): URL for cleanup
    """

    # value is coming with url-encoding and "?" is appearing as %3F.
    value = urllib.unquote(value)
    return value.split('?')[0] if '?' in value else value
