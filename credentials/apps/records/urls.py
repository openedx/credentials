from django.conf.urls import url

from credentials.apps.credentials.constants import UUID_PATTERN

from . import views

urlpatterns = [
    url(r'^$', views.RecordsView.as_view(), name='index'),
    url(r'^programs/{uuid}/$'.format(uuid=UUID_PATTERN), views.ProgramRecordView.as_view(), {'is_public': False},
        name='private_programs'),
    url(r'^programs/shared/{uuid}/$'.format(uuid=UUID_PATTERN), views.ProgramRecordView.as_view(), {'is_public': True},
        name='public_programs'),
    url(r'^new/$', views.ProgramRecordCreationView.as_view(), name='cert_creation'),
]
