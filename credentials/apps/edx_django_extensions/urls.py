from django.urls import path

from credentials.apps.edx_django_extensions import views


urlpatterns = [
    path(r"^$", views.ManagementView.as_view(), name="index"),
]
