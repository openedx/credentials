"""
Template tags and helper functions for escaping script tag.
"""
from django import template
from django.template.defaultfilters import date
from django.utils.translation import get_language
register = template.Library()


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
