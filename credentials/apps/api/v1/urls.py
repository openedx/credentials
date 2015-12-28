""" API v1 URLs. """
from rest_framework.routers import DefaultRouter

from credentials.apps.api.v1 import views


router = DefaultRouter()  # pylint: disable=invalid-name
router.register(r'user_credentials', views.UserCredentialViewSet)
router.register(r'program_credentials', views.CredentialsByProgramsViewSet, base_name='program_credentials')
router.register(r'course_credentials', views.CredentialsByCoursesViewSet, base_name='course_credentials')

urlpatterns = router.urls
