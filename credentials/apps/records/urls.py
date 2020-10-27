from django.conf.urls import url

from credentials.apps.credentials.constants import UUID_PATTERN

from . import views


urlpatterns = [
    url(r'^$', views.RecordsView.as_view(), name='index'),
    url(fr'^programs/{UUID_PATTERN}/$', views.ProgramRecordView.as_view(), {'is_public': False},
        name='private_programs'),
    url(fr'^programs/shared/{UUID_PATTERN}/$', views.ProgramRecordView.as_view(), {'is_public': True},
        name='public_programs'),
    url(fr'^programs/shared/{UUID_PATTERN}/csv$',
        views.ProgramRecordCsvView.as_view(),
        name='program_record_csv'),
    url(fr'^programs/{UUID_PATTERN}/send$', views.ProgramSendView.as_view(), name='send_program'),
    url(fr'^programs/{UUID_PATTERN}/share$', views.ProgramRecordCreationView.as_view(),
        name='share_program'),
]
