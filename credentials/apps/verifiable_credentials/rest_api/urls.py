"""Root API URLs for verifiable_credentials."""

from django.urls import include, path


urlpatterns = [
    path("v1/", include(("credentials.apps.verifiable_credentials.rest_api.v1.urls", "v1"), namespace="v1")),
]
