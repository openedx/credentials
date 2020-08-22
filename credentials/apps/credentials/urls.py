"""
URLs for the credentials views.
"""
from django.conf.urls import url

from credentials.apps.credentials import views
from credentials.apps.credentials.constants import UUID_PATTERN

urlpatterns = [
    url(r"^example/$", views.ExampleCredential.as_view(), name="example"),
    url(
        r"^{uuid}/$".format(uuid=UUID_PATTERN),
        views.RenderCredential.as_view(),
        name="render",
    ),
]
