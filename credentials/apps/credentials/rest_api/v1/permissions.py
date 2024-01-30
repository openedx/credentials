"""
Permission classes for Credentials API
"""

from django.conf import settings
from rest_framework import permissions


class CanGetLearnerStatus(permissions.BasePermission):
    """
    Grant access to the learner status API for the service user, and to superusers.
    """

    def has_permission(self, request, view):
        return request.user.username == settings.LEARNER_STATUS_WORKER or request.user.is_staff
