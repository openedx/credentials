from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.RecordsView.as_view(), name='index'),
]
