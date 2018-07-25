from django.conf.urls import url

from credentials.apps.credentials.constants import UUID_PATTERN

from . import views

urlpatterns = [
    url(r'^$', views.RecordsView.as_view(), name='index'),
    url(r'^programs/{uuid}/$'.format(uuid=UUID_PATTERN), views.ProgramRecordView.as_view(), {'is_public': False},
        name='private_programs'),
    url(r'^programs/shared/{uuid}/$'.format(uuid=UUID_PATTERN), views.ProgramRecordView.as_view(), {'is_public': True},
        name='public_programs'),
    url(r'^programs/shared/{uuid}/csv$'.format(uuid=UUID_PATTERN),
        views.ProgramRecordCsvView.as_view(),
        name='program_record_csv'),
    url(r'^programs/{uuid}/send$'.format(uuid=UUID_PATTERN), views.ProgramSendView.as_view(), name='send_program'),
    url(r'^programs/{uuid}/share$'.format(uuid=UUID_PATTERN), views.ProgramRecordCreationView.as_view(),
        name='share_program'),
    # Test urls
    url(r'^test_hijack/$'.format(uuid=UUID_PATTERN), views.UsernameHijackView.as_view(),
        name='test_hijack'),
]
