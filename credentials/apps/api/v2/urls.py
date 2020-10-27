from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from credentials.apps.api.v2 import views


urlpatterns = [
    url(r'^replace_usernames/$', views.UsernameReplacementView.as_view(), name="replace_usernames")
]

router = DefaultRouter()  # pylint: disable=invalid-name
# URLs can not have hyphen as it is not currently supported by slumber
# as mentioned https://github.com/samgiles/slumber/issues/44
router.register(r'credentials', views.CredentialViewSet, basename='credentials')
router.register(r'grades', views.GradeViewSet, basename='grades')
urlpatterns += router.urls
