from django.conf.urls import include
from django.urls import re_path
from . import views


urlpatterns = [
    re_path(r"^$", views.RecordsView.as_view(), name="index"),
    re_path(r"^api/", include(("credentials.apps.records.rest_api.urls", "api"), namespace="api")),
]
