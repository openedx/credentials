"""
Template tags and helper functions for escaping script tag.
"""
from django import template
from django.template.defaultfilters import date
from django.utils import html
from django.utils.translation import get_language
register = template.Library()


@register.filter(name="htmlescape")
def htmlescape(value):
    escaped_msg = html.escape(value)
    return escaped_msg


@register.simple_tag(name="interpolate_html")
def interpolate_html(value, **kwargs):
    """
    Interpolates HTML into a string.

    Arguments:
        value (string): a string to escape and format.
        kwargs: named arguments to be formatted into the 'value' argument
            NOTE: kwargs will be escaped unless they are marked safe
            (Developers passing safe HTML as kwargs should first pass the value through the |safe filter)

    Returns:
        SafeString: A formatted and escaped version 'value' with all kwargs escaped appropriately
    """
    escaped_msg = html.escape(value)
    safe_interpolated_msg = html.format_html(escaped_msg, **kwargs)
    return safe_interpolated_msg


@register.filter(expects_localtime=True, is_safe=False)
def month(value):
    """
    Provides the month from a provided date as a string.

    This is used to work around a bug in the Spanish django month translations.
    See LEARNER-3859 for more details.

    Arguments:
        value (datetime): date to format

    Returns:
        string: A formatted version of the month
    """
    formatted = date(value, 'E')

    language = get_language()
    if language and language.split('-')[0].lower() == 'es':
        return formatted.lower()

    return formatted
