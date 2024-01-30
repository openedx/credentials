"""
URLs for verifiable_credentials.
"""

from django.urls import include, path


urlpatterns = [
    path("api/", include(("credentials.apps.verifiable_credentials.rest_api.urls", "api"), namespace="api")),
]
