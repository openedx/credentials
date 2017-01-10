from rest_framework.routers import DefaultRouter

from credentials.apps.api.v2 import views

router = DefaultRouter()  # pylint: disable=invalid-name
# URLs can not have hyphen as it is not currently supported by slumber
# as mentioned https://github.com/samgiles/slumber/issues/44
router.register(r'credentials', views.CredentialViewSet, base_name='credentials')

urlpatterns = router.urls
