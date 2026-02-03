from django.urls import include, path

from credentials.apps.credentials.rest_api.v1 import urls as v1_credentials_api_urls

# NOTE: Although this is v1 and other APIs in this application are v2,
# the API naming and code layout convention here is what we are using, per
# https://openedx.atlassian.net/wiki/spaces/AC/pages/18350757/edX+REST+API+Conventions
urlpatterns = [
    path("v1/", include((v1_credentials_api_urls, "v1"), namespace="v1")),
]
