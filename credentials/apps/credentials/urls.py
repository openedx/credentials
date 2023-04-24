"""
URLs for the credentials views.
"""
from django.conf.urls import include, url
from django.urls import re_path

from credentials.apps.credentials import views
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.rest_api.v1 import urls as credentials_api_v1_urls


urlpatterns = [
    re_path(r"^example/$", views.ExampleCredential.as_view(), name="example"),
    re_path(rf"^example/{UUID_PATTERN}/$", views.RenderExampleProgramCredential.as_view(), name="render_example"),
    re_path(rf"^{UUID_PATTERN}/$", views.RenderCredential.as_view(), name="render"),
    url(r"^api/", include((credentials_api_v1_urls, "api"), namespace="api")),
]
