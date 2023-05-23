"""Root API URLs for verifiable_credentials."""
from django.conf.urls import include
from django.urls import re_path


urlpatterns = [
    re_path(r"^v1/", include(("credentials.apps.verifiable_credentials.rest_api.v1.urls", "v1"), namespace="v1")),
]
