from django.conf.urls import url

from credentials.apps.credentials.rest_api.v1.views import LearnerCertificateStatusView


urlpatterns = [
    url(
        r"^learner_cert_status/$",
        LearnerCertificateStatusView.as_view(),
        name="learner_cert_status",
    )
]
