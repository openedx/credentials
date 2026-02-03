from django.urls import path
from rest_framework.routers import DefaultRouter

from credentials.apps.api.v2 import views

# NOTE: Although this is v2 and other APIs in this application are v1,
# the API naming and code layout convention here is not to be used for new
# endpoints, per:
# https://openedx.atlassian.net/wiki/spaces/AC/pages/18350757/edX+REST+API+Conventions

urlpatterns = [path("replace_usernames/", views.UsernameReplacementView.as_view(), name="replace_usernames")]

router = DefaultRouter()
# URLs can not have hyphen as it is not currently supported by slumber
# as mentioned https://github.com/samgiles/slumber/issues/44
router.register(r"credentials", views.CredentialViewSet, basename="credentials")
router.register(r"grades", views.GradeViewSet, basename="grades")
router.register(r"course_certificates", views.CourseCertificateViewSet, basename="course_certificates")
urlpatterns += router.urls
