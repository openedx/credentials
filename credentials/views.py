from urllib.parse import urljoin

from django.views.generic.base import RedirectView
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.permissions import IsStaff
from rest_framework import permissions, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response


class FaviconView(RedirectView):
    """
    Redirects to the favicon from the LMS
    """
    def get_redirect_url(self, *_args, **_kwargs):
        site_configuration = self.request.site.siteconfiguration
        if not site_configuration.homepage_url:
            return None
        return urljoin(site_configuration.homepage_url, '/favicon.ico')


class MockToggleStateView(views.APIView):  # pragma: no cover
    """
    A mock endpoint showing that we can require a staff JWT in this IDA,
    and allowing us to test integration of multiple IDAs into toggle state
    reports (ARCHBOM-1569). This can go away once edx-toggles is ready and
    integrated.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsStaff,)

    def get(self, request):
        return Response({
            "waffle_flags": [
                {
                    "name": "mock.flag",
                    "class": "WaffleFlag",
                    "module": "mock.core.djangoapps.fake",
                    "code_owner": "platform-arch",
                    "computed_status": "off"
                }
            ],
            "waffle_switches": [],
            "django_settings": [
                {
                    "name": "MOCK_DEBUG",
                    "is_active": False
                },
                {
                    "name": "OTHER_MOCK['stuff']",
                    "is_active": True
                }
            ]
        })
