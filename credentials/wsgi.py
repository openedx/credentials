"""
WSGI config for credentials.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
from os.path import abspath, dirname
from sys import path

from django.core.wsgi import get_wsgi_application


SITE_ROOT = dirname(dirname(abspath(__file__)))
path.append(SITE_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "credentials.settings.local")

application = get_wsgi_application()  # pylint: disable=invalid-name
