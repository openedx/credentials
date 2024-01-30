"""
Custom permissions classes for use with DRF.
"""

from django.conf import settings
from rest_framework import permissions


class UserCredentialPermissions(permissions.DjangoModelPermissions):
    """
    Custom extension to DjangoModelPermissions for use with UserCredential objects.

    - The `list` action requires an explicit view_usercredential permission to be set for the user.
    - The `retrieve` action is accessible to anyone with the permission above OR whose username corresponds to the
        UserCredential object's username field.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }

    def has_object_permission(self, request, view, obj):
        """
        Allow access to specific objects when granted explicitly (via model
        permissions) or, if a read-only request, implicitly (via matching
        username).
        """
        return super().has_permission(request, view) or request.user.username.lower() == obj.username.lower()

    def has_permission(self, request, view):
        default = super().has_permission(request, view)
        filtered_username = request.query_params.get("username", "").lower()

        if request.method == "GET" and view.action == "list" and filtered_username:
            return default or (request.user.username.lower() == filtered_username)

        return default


class CanReplaceUsername(permissions.BasePermission):
    """
    Grants access to the Username Replacement API for the service user.
    """

    def has_permission(self, request, view):
        return request.user.username == settings.USERNAME_REPLACEMENT_WORKER
