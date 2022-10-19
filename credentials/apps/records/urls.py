from django.conf.urls import include
from django.urls import re_path

from credentials.apps.credentials.constants import UUID_PATTERN

from . import views


urlpatterns = [
    re_path(r"^$", views.RecordsView.as_view(), name="index"),
    re_path(r"^api/", include(("credentials.apps.records.rest_api.urls", "api"), namespace="api")),
    # TODO: We should be able to remove this as part of https://github.com/openedx/credentials/issues/1722
    re_path(
        rf"^programs/{UUID_PATTERN}/$", views.ProgramRecordView.as_view(), {"is_public": False}, name="private_programs"
    ),
    # NOTE: We need to _keep_ this to ensure shared public program records continue to work
    re_path(
        rf"^programs/shared/{UUID_PATTERN}/$",
        views.ProgramRecordView.as_view(),
        {"is_public": True},
        name="public_programs",
    ),
    re_path(rf"^programs/shared/{UUID_PATTERN}/csv$", views.ProgramRecordCsvView.as_view(), name="program_record_csv"),
    re_path(rf"^programs/{UUID_PATTERN}/send$", views.ProgramSendView.as_view(), name="send_program"),
    re_path(rf"^programs/{UUID_PATTERN}/share$", views.ProgramRecordCreationView.as_view(), name="share_program"),
]
