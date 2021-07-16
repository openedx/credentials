from django.urls import re_path

from credentials.apps.records.rest_api.v1 import views


urlpatterns = [
    re_path(r"^program_records/$", views.ProgramRecords.as_view(), name="program_records"),
]
