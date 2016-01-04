"""
URLs for the credentials views.
"""
from django.conf.urls import url
from credentials.apps.credentials.constants import UUID_PATTERN
from credentials.apps.credentials.views import RenderCredential

urlpatterns = [
    url(r'^{uuid}/$'.format(uuid=UUID_PATTERN),
        RenderCredential.as_view(), name='render'),
]
