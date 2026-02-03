from rest_framework import routers

from credentials.apps.records.rest_api.v1 import views

router = routers.DefaultRouter()
router.register(r"program_records", views.ProgramRecordsViewSet, basename="records")

urlpatterns = []

urlpatterns += router.urls
