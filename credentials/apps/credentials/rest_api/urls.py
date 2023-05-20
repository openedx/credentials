from django.urls import path
from django.urls import include

from credentials.apps.credentials.rest_api.v1 import urls as v1_credentials_api_urls


urlpatterns = [
    path("v1/", include((v1_credentials_api_urls, "v1"), namespace="v1")),
]
