from django.conf.urls import url

from credentials.apps.edx_django_extensions import views


urlpatterns = [
    url(r'^$', views.ManagementView.as_view(), name='index'),
]
