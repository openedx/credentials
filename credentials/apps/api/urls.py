"""
Root API URLs.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""

from django.urls import include, path


urlpatterns = [
    path("v2/", include(("credentials.apps.api.v2.urls", "v2"), namespace="v2")),
]
