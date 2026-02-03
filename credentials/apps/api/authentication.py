"""
Authentication logic for REST API.
"""

import logging

import edx_rest_framework_extensions.auth.jwt.authentication as edx_drf_auth
from django.contrib.auth.models import Group

from credentials.apps.core.constants import Role

logger = logging.getLogger(__name__)


def _set_user_roles(user, payload):
    """
    DRY helper - sets roles for a user based on JWT payload (during JWT auth)
    or social auth signin (for use with session auth in the browseable API).
    """
    admin_group = Group.objects.get(name=Role.ADMINS)
    if payload.get("administrator"):
        user.groups.add(admin_group)
    else:
        user.groups.remove(admin_group)


def pipeline_set_user_roles(response, user=None, *_, **__):  # pylint: disable=keyword-arg-before-vararg
    """
    Social auth pipeline function to update group memberships based
    on claims present in the id token.
    """
    if user:
        _set_user_roles(user, response)
        return {"user": user}
    return {}


class JwtAuthentication(edx_drf_auth.JwtAuthentication):
    """
    Overrides the default JwtAuthentication class to ensure that admin users are added to the admin group.
    """

    def authenticate_credentials(self, payload):
        """
        Return the user object with the admin group added or removed if the user is an admin.
        """
        user = super().authenticate_credentials(payload)
        admin_group = Group.objects.get(name=Role.ADMINS)
        if payload.get("administrator"):
            user.groups.add(admin_group)
        else:
            user.groups.remove(admin_group)
        return user
