from django.urls import re_path

from credentials.apps.credentials.rest_api.v1.views import LearnerCertificateStatusView


urlpatterns = [
    re_path(
        r"^learner_cert_status/$",
        LearnerCertificateStatusView.as_view(),
        name="learner_cert_status",
    )
]
