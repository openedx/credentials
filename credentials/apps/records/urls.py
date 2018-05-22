from django.conf.urls import url

from credentials.apps.credentials.constants import UUID_PATTERN

from . import views

urlpatterns = [
    url(r'^$', views.RecordsView.as_view(), name='index'),
    url(r'^programs/{uuid}/$'.format(uuid=UUID_PATTERN), views.ProgramRecordView.as_view(), name='programs'),
]
