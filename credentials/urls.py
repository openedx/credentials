"""credentials URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

import os

from auth_backends.urls import auth_urlpatterns
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin

from credentials.apps.core import views as core_views

admin.autodiscover()


urlpatterns = auth_urlpatterns + [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('credentials.apps.api.urls', namespace='api')),
    url(r'^api-auth/', include(auth_urlpatterns, namespace='rest_framework')),
    url(r'^auto_auth/$', core_views.AutoAuth.as_view(), name='auto_auth'),
    url(r'^credentials/', include('credentials.apps.credentials.urls', namespace='credentials')),
    url(r'^health/$', core_views.health, name='health'),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', ''),
]

handler500 = 'credentials.apps.core.views.render_500'

# Add media and extra urls
if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^404/$', 'django.views.defaults.page_not_found', name='404'),
        url(r'^500/$', handler500, name='500'),
    ]

if settings.DEBUG and os.environ.get('ENABLE_DJANGO_TOOLBAR', False):  # pragma: no cover
    import debug_toolbar  # pylint: disable=import-error, wrong-import-position, wrong-import-order

    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
