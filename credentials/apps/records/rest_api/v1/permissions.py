"""
Custom permissions classes for use with DRF.
"""

from edx_rest_framework_extensions.permissions import get_username_param
from rest_framework import permissions


class IsPublic(permissions.BasePermission):
    """
    Allows access if URL is for a public record.
    """

    def has_permission(self, request, view):
        """
        Check to see what type of record (private/public) in the query parameter.
        If it is not public, run a normal authentication permission check.
        """
        query_param_is_public = request.query_params.get("is_public", "")
        is_public = query_param_is_public.lower() == "true"
        if not is_public:
            return bool(request.user and request.user.is_authenticated)
        return True


class CanAccessProgramRecord(permissions.BasePermission):
    """
    Allows access if the requesting user a staff member or a superuser.
    """

    def has_permission(self, request, view):
        """
        If there is a username query param, check for either superuser or staff access.
        """
        if get_username_param(request):
            return request.user and (request.user.is_superuser or request.user.is_staff)
        return True
