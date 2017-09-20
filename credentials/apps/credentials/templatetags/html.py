"""
Template tags and helper functions for escaping script tag.
"""
from django import template
from django.utils import html
register = template.Library()


@register.filter(name="htmlescape")
def escape(value):
    escaped_msg = html.escape(value)

    html_style = {
        'StartSpan': '<span class=\"accomplishment-statement-detail copy\">',
        'EndSpan': '</span>',
        'StrongStart': '<strong class=\"accomplishment-recipient\">',
        'StrongEnd': '</strong>'
    }
    escaped_styled_msg = escaped_msg.format(**html_style)
    return escaped_styled_msg
