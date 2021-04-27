from django.urls import re_path
from rest_framework.routers import DefaultRouter

from credentials.apps.api.v2 import views


urlpatterns = [re_path(r"^replace_usernames/$", views.UsernameReplacementView.as_view(), name="replace_usernames")]

router = DefaultRouter()
# URLs can not have hyphen as it is not currently supported by slumber
# as mentioned https://github.com/samgiles/slumber/issues/44
router.register(r"credentials", views.CredentialViewSet, basename="credentials")
router.register(r"grades", views.GradeViewSet, basename="grades")
router.register(r"course_certificates", views.CourseCertificateViewSet, basename="course_certificates")
urlpatterns += router.urls
