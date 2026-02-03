"""
Verifiable Credentials API v1 URLs.
"""

from django.urls import path
from rest_framework import routers

from credentials.apps.verifiable_credentials.rest_api.v1 import views

router = routers.DefaultRouter()
router.register(r"credentials", views.CredentialsViewSet, basename="credentials")

urlpatterns = [
    path(r"credentials/init/", views.InitIssuanceView.as_view(), name="credentials-init"),
    path(
        r"credentials/issue/<uuid:issuance_line_uuid>/",
        views.IssueCredentialView.as_view(),
        name="credentials-issue",
    ),
    path(r"storages/", views.AvailableStoragesView.as_view(), name="storages"),
    path(r"status-list/2021/v1/<str:issuer_id>/", views.StatusList2021View.as_view(), name="status-list-2021-v1"),
]

urlpatterns += router.urls
