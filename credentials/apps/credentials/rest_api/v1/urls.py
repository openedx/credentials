from django.urls import path

from credentials.apps.credentials.rest_api.v1.views import (
    BulkLearnerCertificateStatusView,
    LearnerCertificateStatusView,
)


urlpatterns = [
    path(
        "learner_cert_status/",
        LearnerCertificateStatusView.as_view(),
        name="learner_cert_status",
    ),
    path(
        "bulk_learner_cert_status/",
        BulkLearnerCertificateStatusView.as_view(),
        name="bulk_learner_cert_status",
    ),
]
