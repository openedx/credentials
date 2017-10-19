"""
Template tags and helper functions for escaping script tag.
"""
from django import template
from django.utils import html
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
