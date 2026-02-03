"""
Template tags and helper functions for creating language tagged files
"""

import logging
from os.path import splitext

from django import template
from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.utils.translation import get_language

register = template.Library()
logger = logging.getLogger(__name__)


@register.filter(name="translate_file_path")
def translate_file_path(filepath):
    """
    Uses the filepath parameter to construct a set of potential language suffixed file names, and return
    the template_name of the first template matching the current language, default language if otherwise,
    or if neither the base path requested. Throws a TemplateNotFound exception if none are found.

    The format necessary for filepath should match 'some/path/filename.svg'
    This will search for 'some/path/filename-**.svg' where ** is the requested/default language tags.
    """
    paths = construct_file_language_names(filepath, get_language())
    try:
        return select_template(paths).origin.template_name
    except TemplateDoesNotExist:
        logger.error(f"Could not find translation template in [{paths}]")
        raise


def construct_file_language_names(filepath, language, default=settings.LANGUAGE_CODE):
    """
    Creates an array containing between two and five strings in a guaranteed order:
        1. The requested language added before the svg suffix (e.g. filepath-es-419.svg)
        2. (optional) The requested language two character code added before the svg suffix (e.g. filepath-es.svg)
        3. (optional) The default language added before the svg suffix (e.g. filepath-en-US.svg)
        4. (optional) The default language two character code added before the svg suffix (e.g. filepath-en.svg)
        5. The unmodified requested filepath (e.g. filepath.svg)
    """
    # Replace out underscores so languages are always consistently named with hyphens
    replaced_language = language.replace("_", "-")
    replaced_default = default.replace("_", "-")

    root, ext = splitext(filepath)
    paths = []
    if language:
        paths.append(f"{root}-{replaced_language}{ext}")

        # If the requested language is longer than just the two character language code, add the 2 char substring
        if len(language) > 2:
            paths.append("{}-{}{}".format(root, replaced_language[:2], ext))

    # If the requested language and the default are different, add the default language to the paths
    if language != default:
        paths.append(f"{root}-{replaced_default}{ext}")

        # If the default language is longer than just the two character language code, add the 2 char substring as well
        if len(default) > 2 and language[:2] != default[:2]:
            paths.append("{}-{}{}".format(root, replaced_default[:2], ext))

    # Always add the base requested filepath to the end of the array
    paths.append(filepath)
    return paths
