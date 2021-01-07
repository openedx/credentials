from django.urls import re_path

from credentials.apps.edx_django_extensions import views


urlpatterns = [
    re_path(r"^$", views.ManagementView.as_view(), name="index"),
]
