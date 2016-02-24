"""
Authentication logic for REST API.
"""

import logging

import requests
from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.status import HTTP_200_OK
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


class BearerAuthentication(BaseAuthentication):
    """Simple token based authentication. Clients should authenticate by passing the token
    key in the "Authorization" HTTP header, prepended with the string "Bearer ".  For example:

    Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """

    def authenticate(self, request):
        provider_url = getattr(settings, 'OAUTH2_PROVIDER_URL', None)
        if not provider_url:
            return None

        provider_url = provider_url.strip('/')
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'bearer':
            return None

        if len(auth) == 1:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth) > 2:
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        return self.authenticate_credentials(provider_url, auth[1])

    def authenticate_credentials(self, provider_url, key):
        """
        Authenticate the access token key. Return the user and key

        Args:
            key (string): Access token key

        Returns:
            user object and access token key.
        """
        try:
            response = requests.get('{}/access_token/{}/'.format(provider_url, key))
            if response.status_code != HTTP_200_OK:
                raise AuthenticationFailed('Invalid token.')

            data = response.json()
            user = User.objects.get(username=data['username'])  # pylint: disable=no-member
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid token.')

        if not user.is_active:
            raise AuthenticationFailed('User inactive or deleted.')

        return user, key

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`.
        """
        return 'Bearer'
