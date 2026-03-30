"""
Template tag for referencing uploaded CertificateAsset files inside
DB-backed ProgramCertificateTemplate HTML.

Usage::

    {% load certificate_assets %}

    {# Renders the asset URL, empty string if slug not found #}
    <img src="{% certificate_asset_url 'fbr-logo' %}" alt="FBR Logo">

    {# CSS file #}
    <link rel="stylesheet" href="{% certificate_asset_url 'custom-cert-styles' %}">

    {# Font #}
    <style>
      @font-face {
        font-family: 'CustomFont';
        src: url("{% certificate_asset_url 'custom-font-regular' %}") format('woff2');
      }
    </style>
"""

import logging

from django import template

log = logging.getLogger(__name__)

register = template.Library()


@register.simple_tag
def certificate_asset_url(slug):
    """
    Return the URL of the CertificateAsset with the given slug.

    Returns an empty string and logs a warning if the slug does not exist,
    so a missing asset degrades gracefully rather than crashing the certificate page.
    """
    # Import inside the function to avoid import-time issues when this tag
    # is loaded by from_string() before the app registry is fully ready.
    from credentials.apps.credentials.models import CertificateAsset  # noqa: PLC0415

    try:
        asset = CertificateAsset.objects.get(slug=slug)
        return asset.asset.url
    except CertificateAsset.DoesNotExist:
        log.warning("certificate_asset_url: no CertificateAsset found with slug=%r", slug)
        return ""
