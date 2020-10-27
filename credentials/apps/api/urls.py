"""
Root API URLs.

All API URLs should be versioned, so urlpatterns should only
contain namespaces for the active versions of the API.
"""
from django.conf.urls import include, url


urlpatterns = [
    url(r'^v2/', include(('credentials.apps.api.v2.urls', 'v2'), namespace='v2')),
]
