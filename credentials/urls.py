"""credentials URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URL
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include(blog_urls))
"""

import os

from auth_backends.urls import oauth2_urlpatterns
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.utils.translation import gettext_lazy as _
from django.views.defaults import page_not_found
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from edx_django_utils.plugins import get_plugin_url_patterns
from rest_framework import permissions

from credentials.apps.core import views as core_views
from credentials.apps.plugins.constants import PROJECT_TYPE
from credentials.apps.records.views import ProgramListingView
from credentials.views import FaviconView, MockToggleStateView


admin.autodiscover()
admin.site.site_header = _("Credentials Administration")
admin.site.site_title = admin.site.site_header

schema_view = get_schema_view(
    openapi.Info(
        title="Credentials API",
        default_version="v1",
        description="Credentials API docs",
    ),
    public=False,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = oauth2_urlpatterns + [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^api/", include(("credentials.apps.api.urls", "api"), namespace="api")),
    re_path(r"^api-auth/", include((oauth2_urlpatterns, "rest_framework"), namespace="rest_framework")),
    re_path(r"^api-docs/$", schema_view.with_ui("swagger", cache_timeout=0), name="api_docs"),
    re_path(r"^auto_auth/$", core_views.AutoAuth.as_view(), name="auto_auth"),
    re_path(r"^credentials/", include(("credentials.apps.credentials.urls", "credentials"), namespace="credentials")),
    re_path(r"^health/$", core_views.health, name="health"),
    re_path(
        r"^management/", include(("credentials.apps.edx_django_extensions.urls", "management"), namespace="management")
    ),
    re_path(r"^records/", include(("credentials.apps.records.urls", "records"), namespace="records")),
    re_path(r"^program-listing/", ProgramListingView.as_view(), name="program_listing"),
    re_path(r"^favicon\.ico$", FaviconView.as_view(permanent=True)),
    re_path(r"^mock-toggles$", MockToggleStateView.as_view()),
    re_path(r"^hijack/", include("hijack.urls", namespace="hijack")),
]

# edx-drf-extensions csrf app
urlpatterns += [
    path("", include("csrf.urls")),
]

handler500 = "credentials.apps.core.views.render_500"

# Add media and extra urls
if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        re_path(r"^404/$", page_not_found, name="404"),
        re_path(r"^500/$", core_views.render_500, name="500"),
    ]

if settings.DEBUG and os.environ.get("ENABLE_DJANGO_TOOLBAR", False):  # pragma: no cover
    import debug_toolbar

    urlpatterns.append(re_path(r"^__debug__/", include(debug_toolbar.urls)))

# Plugin django app urls
urlpatterns.extend(get_plugin_url_patterns(PROJECT_TYPE))
