from django.urls import re_path

from credentials.apps.credentials.constants import UUID_PATTERN

from . import views


urlpatterns = [
    re_path(r'^$', views.RecordsView.as_view(), name='index'),
    re_path(fr'^programs/{UUID_PATTERN}/$', views.ProgramRecordView.as_view(), {'is_public': False},
            name='private_programs'),
    re_path(fr'^programs/shared/{UUID_PATTERN}/$', views.ProgramRecordView.as_view(), {'is_public': True},
            name='public_programs'),
    re_path(fr'^programs/shared/{UUID_PATTERN}/csv$',
            views.ProgramRecordCsvView.as_view(),
            name='program_record_csv'),
    re_path(fr'^programs/{UUID_PATTERN}/send$', views.ProgramSendView.as_view(), name='send_program'),
    re_path(fr'^programs/{UUID_PATTERN}/share$', views.ProgramRecordCreationView.as_view(),
            name='share_program'),
]
