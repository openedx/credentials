"""
URLs for verifiable_credentials.
"""
from django.conf.urls import include
from django.urls import re_path


urlpatterns = [
    re_path(r"^api/", include(("credentials.apps.verifiable_credentials.rest_api.urls", "api"), namespace="api")),
]
