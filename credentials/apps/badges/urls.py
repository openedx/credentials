"""
URLs for badges.
"""

from django.urls import path

from .credly.webhooks import CredlyWebhook

urlpatterns = [
    path("credly/webhook/", CredlyWebhook.as_view(), name="credly-webhook"),
]
