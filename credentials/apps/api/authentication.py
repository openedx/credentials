"""
Authentication logic for REST API.
"""

import logging

from django.contrib.auth.models import Group
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from credentials.apps.core.constants import Role
from credentials.apps.core.models import User


logger = logging.getLogger(__name__)


def _set_user_roles(user, payload):
    """
    DRY helper - sets roles for a user based on JWT payload (during JWT auth)
    or social auth signin (for use with session auth in the browseable API).
    """
    admin_group = Group.objects.get(name=Role.ADMINS)  # pylint: disable=no-member
    if payload.get('administrator'):
        user.groups.add(admin_group)
    else:
        user.groups.remove(admin_group)


def pipeline_set_user_roles(response, user=None, *_, **__):
    """
    Social auth pipeline function to update group memberships based
    on claims present in the id token.
    """
    if user:
        _set_user_roles(user, response)
        return {'user': user}
    else:
        return {}


class JwtAuthentication(JSONWebTokenAuthentication):
    """
    Custom authentication using JWT from the edx oidc provider.
    """

    def authenticate_credentials(self, payload):
        """
        Return a user object to be associated with the present request, based on
        the content of an already-decoded / verified JWT payload.
        In the process of inflating the user object based on the payload, we also
        make sure that the roles associated with this user are up-to-date.
        """
        if 'preferred_username' not in payload:
            logger.warning('Invalid JWT payload: preferred_username not present.')
            raise AuthenticationFailed()
        username = payload['preferred_username']
        user, __ = User.objects.get_or_create(username=username)  # pylint: disable=no-member
        admin_group = Group.objects.get(name=Role.ADMINS)  # pylint: disable=no-member
        if payload.get('administrator'):
            user.groups.add(admin_group)
        else:
            user.groups.remove(admin_group)

        return user
