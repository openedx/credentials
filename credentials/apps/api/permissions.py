"""
Custom permissions classes for use with DRF.
"""

from django.http import Http404
from rest_framework import permissions


class UserCredentialViewSetPermissions(permissions.DjangoModelPermissions):
    """
    Custom extension to DjangoModelPermissions for use with the
    UserCredentialViewSet.

    This permissions class uses an explicit 'view' permission, enabling support
    for:
        - explicitly granting certain users read access to any UserCredential
        - implicitly granting any user read access to UserCredentials that were
          awarded specifically to them
        - denying read access (obscured by HTTP 404) in any other case

    NOTE: users are allowed to read their own UserCredential records regardless
        of their 'status' (i.e. even if revoked).

    WARNING: this permissions implementation does not cover the 'list' method
        of access.  The access control required under DRF for that use case is
        presently implemented in the `list` method of the viewset itself.
    """

    # refer to the super() for more context on what this override is doing.
    perms_map = permissions.DjangoModelPermissions.perms_map
    perms_map.update({method: ["%(app_label)s.view_%(model_name)s"] for method in permissions.SAFE_METHODS})

    def has_permission(self, request, view):
        """
        Relax the base's view-level permissions in the case of 'safe'
        (read-only) methods, requiring only that the user be authenticated.

        This lets us delay deciding whether or not read permission should be
        implicitly granted, until after DRF has fetched the requested object.
        """
        return super().has_permission(request, view) or (
            request.user.is_authenticated and request.method in permissions.SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        """
        Allow access to specific objects when granted explicitly (via model
        permissions) or, if a read-only request, implicitly (via matching
        username).
        """
        if super().has_permission(request, view):
            return True
        if request.user.username.lower() == obj.username.lower():
            return True
        raise Http404
