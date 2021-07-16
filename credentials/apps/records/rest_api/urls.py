from django.conf.urls import include
from django.urls import re_path

from credentials.apps.records.rest_api.v1 import urls as v1_records_rest_api_urls


urlpatterns = [
    re_path(r"^v1/", include((v1_records_rest_api_urls, "v1"), namespace="v1")),
]
