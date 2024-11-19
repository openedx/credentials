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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from django.views.defaults import page_not_found
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from edx_django_utils.plugins import get_plugin_url_patterns
from rest_framework import permissions

from credentials.apps.badges.toggles import is_badges_enabled
from credentials.apps.core import views as core_views
from credentials.apps.plugins.constants import PROJECT_TYPE
from credentials.apps.records.views import ProgramListingView
from credentials.apps.verifiable_credentials.toggles import is_verifiable_credentials_enabled
from credentials.views import FaviconView


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
    path(
        "api/credentials/",
        include(("credentials.apps.credentials.rest_api.urls", "credentials_api"), namespace="credentials_api"),
    ),
    path("api/", include(("credentials.apps.api.urls", "api"), namespace="api")),
    path("api-auth/", include((oauth2_urlpatterns, "rest_framework"), namespace="rest_framework")),
    path("api-docs/", schema_view.with_ui("swagger", cache_timeout=0), name="api_docs"),
    path("auto_auth/", core_views.AutoAuth.as_view(), name="auto_auth"),
    path("credentials/", include(("credentials.apps.credentials.urls", "credentials"), namespace="credentials")),
    path("health/", core_views.health, name="health"),
    path("management/", include(("credentials.apps.edx_django_extensions.urls", "management"), namespace="management")),
    path("records/", include(("credentials.apps.records.urls", "records"), namespace="records")),
    re_path(r"^program-listing/", ProgramListingView.as_view(), name="program_listing"),
    re_path(r"^favicon\.ico$", FaviconView.as_view(permanent=True)),
]

if is_verifiable_credentials_enabled():
    urlpatterns += [
        path(
            "verifiable_credentials/",
            include(
                ("credentials.apps.verifiable_credentials.urls", "verifiable_credentials"),
                namespace="verifiable_credentials",
            ),
        ),
    ]

if is_badges_enabled():
    urlpatterns += [
        re_path(r"^badges/", include(("credentials.apps.badges.urls", "badges"), namespace="badges")),
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
        path("404/", page_not_found, name="404"),
        path("500/", core_views.render_500, name="500"),
    ]

if settings.DEBUG and os.environ.get("ENABLE_DJANGO_TOOLBAR", False):  # pragma: no cover
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))

# Plugin django app urls
urlpatterns.extend(get_plugin_url_patterns(PROJECT_TYPE))
