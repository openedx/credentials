"""
Authentication logic for REST API.
"""

import logging

from django.conf import settings
from django.contrib.auth.models import Group
from edx_rest_framework_extensions.auth.bearer.authentication import BearerAuthentication as BaseBearerAuthentication
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
    admin_group = Group.objects.get(name=Role.ADMINS)
    if payload.get('administrator'):
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
        return {'user': user}
    return {}


class JwtAuthentication(JSONWebTokenAuthentication):
    """
    Custom authentication using JWT from the edx oauth provider.
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
        user, __ = User.objects.get_or_create(username=username)
        admin_group = Group.objects.get(name=Role.ADMINS)
        if payload.get('administrator'):
            user.groups.add(admin_group)
        else:
            user.groups.remove(admin_group)

        return user


class BearerAuthentication(BaseBearerAuthentication):
    """
    Simple token based authentication.

    This authentication class is useful for authenticating an OAuth2 access token against a remote
    authentication provider. Clients should authenticate by passing the token key in the "Authorization" HTTP header,
    prepended with the string `"Bearer "`.

    NOTE: This authentication class is deprecated, see ARCH-396.
    """
    def get_user_info_url(self):
        """ Returns the URL, hosted by the OAuth2 provider, from which user information can be pulled. """
        return '{base}/user_info/'.format(base=settings.BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL)
