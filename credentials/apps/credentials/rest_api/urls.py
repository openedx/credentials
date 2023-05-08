from django.conf.urls import include, url

from credentials.apps.credentials.rest_api.v1 import urls as v1_credentials_api_urls


urlpatterns = [
    url(r"^v1/", include((v1_credentials_api_urls, "v1"), namespace="v1")),
]
