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

from auth_backends.urls import oauth2_urlpatterns
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.views.defaults import page_not_found
from rest_framework_swagger.views import get_swagger_view

from credentials.apps.core import views as core_views
from credentials.apps.records.views import ProgramListingView
from credentials.views import FaviconView, MockToggleStateView


admin.autodiscover()
admin.site.site_header = _('Credentials Administration')
admin.site.site_title = admin.site.site_header

urlpatterns = oauth2_urlpatterns + [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(('credentials.apps.api.urls', 'api'), namespace='api')),
    url(r'^api-auth/', include((oauth2_urlpatterns, 'rest_framework'), namespace='rest_framework')),
    url(r'^api-docs/', get_swagger_view(title='Credentials API'), name='api_docs'),
    url(r'^auto_auth/$', core_views.AutoAuth.as_view(), name='auto_auth'),
    url(r'^credentials/', include(('credentials.apps.credentials.urls', 'credentials'), namespace='credentials')),
    url(r'^health/$', core_views.health, name='health'),
    url(
        r'^management/', include(('credentials.apps.edx_django_extensions.urls', 'management'), namespace='management')
    ),
    url(r'^records/', include(('credentials.apps.records.urls', 'records'), namespace='records')),
    url(r'^program-listing/', ProgramListingView.as_view(), name='program_listing'),
    url(r'^favicon\.ico$', FaviconView.as_view(permanent=True)),
    url(r'^mock-toggles$', MockToggleStateView.as_view()),
    url(r'^hijack/', include('hijack.urls', namespace='hijack')),
]

handler500 = 'credentials.apps.core.views.render_500'

# Add media and extra urls
if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^404/$', page_not_found, name='404'),
        url(r'^500/$', core_views.render_500, name='500'),
    ]

if settings.DEBUG and os.environ.get('ENABLE_DJANGO_TOOLBAR', False):  # pragma: no cover
    import debug_toolbar

    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
