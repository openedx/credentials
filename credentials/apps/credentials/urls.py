"""
URLs for the credentials views.
"""

from django.urls import path, re_path

from credentials.apps.credentials import views
from credentials.apps.credentials.constants import UUID_PATTERN

urlpatterns = [
    path("example/", views.ExampleCredential.as_view(), name="example"),
    re_path(rf"^example/{UUID_PATTERN}/$", views.RenderExampleProgramCredential.as_view(), name="render_example"),
    re_path(rf"^{UUID_PATTERN}/$", views.RenderCredential.as_view(), name="render"),
]
