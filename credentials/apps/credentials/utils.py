"""
Helper methods for credential app.
"""
import datetime
import hashlib
import logging
from itertools import groupby

import jwt
from django.conf import settings
from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient

log = logging.getLogger(__name__)


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
        attributes (list): List of dicts contains attributes data

    Returns:
        Boolean: Return True only if data has no duplicated namespace and name

    """

    def keyfunc(attribute):  # pylint: disable=missing-docstring
        return attribute['name']

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True


def get_program(program_id):
    """ Retrieve program detail from the Programs API.

    Returned value is cached to avoid calling programs service each time a
    certificate is viewed.

    Arguments:
        program_id (int): Unique id of the program for retrieval

    Returns:
        dict, representing a program data returned by the Programs service.
    """
    cache_key = 'programs.api.data.{id}'.format(id=program_id)
    program = cache.get(cache_key)

    if program:
        return program

    programs_api = get_program_api_client()
    program = programs_api.programs(program_id).get()
    cache.set(cache_key, program, settings.PROGRAMS_CACHE_TTL)

    return program


def get_organization(organization_key):
    """ Retrieve the organization detail from the Organizations API.

    If the API call is successful, the returned data will be cached for the
    duration of ORGANIZATIONS_CACHE_TTL (in seconds). Failed API responses
    will NOT be cached.

    Arguments:
        organization_key (str): Unique key of the organization for retrieval

    Returns:
        dict, representing organization data returned by the LMS.
    """
    cache_key = 'organizations.api.data.{hash}'.format(hash=_make_hash(organization_key))
    organization = cache.get(cache_key)

    if organization:
        return organization

    organizations_api = get_organizations_api_client()
    organization = organizations_api.organizations(organization_key).get()
    cache.set(cache_key, organization, settings.ORGANIZATIONS_CACHE_TTL)

    return organization


def get_user_data(username):
    """ Retrieve the user detail from the User API.

    If the API call is successful, the returned data will be cached for the
    duration of USER_CACHE_TTL (in seconds). Failed API responses will NOT
    be cached.

    Arguments:
        username (str): Unique identifier of the user for retrieval

    Returns:
        dict, representing user data returned by the User API.
    """
    cache_key = 'user.api.data.{hash}'.format(hash=_make_hash(username))
    user = cache.get(cache_key)

    if user:
        return user

    user_api = get_user_api_client()
    user = user_api.accounts(username).get()
    cache.set(cache_key, user, settings.USER_CACHE_TTL)

    return user


def get_program_api_client():
    """
    Return api client to communicate with the programs service by using the
    credentials service user in the programs service.
    """
    programs_api_url = settings.PROGRAMS_API_URL
    service_username = settings.CREDENTIALS_SERVICE_USER
    jwt_audience = settings.PROGRAMS_JWT_AUDIENCE
    jwt_secret_key = settings.PROGRAMS_JWT_SECRET_KEY

    return _get_service_user_api_client(programs_api_url, service_username, jwt_audience, jwt_secret_key)


def get_organizations_api_client():
    """
    Return api client to communicate with the organizations api by using the
    credentials service user in the LMS.
    """
    organizations_api_url = settings.ORGANIZATIONS_API_URL
    service_username = settings.CREDENTIALS_SERVICE_USER
    jwt_audience = settings.ORGANIZATIONS_AUDIENCE
    jwt_secret_key = settings.ORGANIZATIONS_SECRET_KEY

    return _get_service_user_api_client(organizations_api_url, service_username, jwt_audience, jwt_secret_key)


def get_user_api_client():
    """
    Return api client to communicate with the user api by using the credentials
    service user in the LMS.
    """
    user_api_url = settings.USER_API_URL
    service_username = settings.CREDENTIALS_SERVICE_USER
    jwt_audience = settings.USER_JWT_AUDIENCE
    jwt_secret_key = settings.USER_JWT_SECRET_KEY

    # user api don't accept url with trailing slash so make `append_slash` False
    return _get_service_user_api_client(
        user_api_url, service_username, jwt_audience, jwt_secret_key, append_slash=False
    )


def _get_service_user_api_client(api_url, service_username, jwt_audience, jwt_secret_key, **kwargs):
    """
    Helper method to get edx rest api client for the provided service user
    which is present on the system from 'api_url'.

    Arguments:
        api_url (str): Absolute url of the api
        service_username (str): Username of the service user
        jwt_audience (str): JWT key for the api auth
        jwt_secret_key (str): JWT secret key for the api auth

    """
    now = datetime.datetime.utcnow()
    expires_in = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)
    payload = {
        'preferred_username': service_username,
        'username': service_username,
        'iss': settings.SOCIAL_AUTH_EDX_OIDC_URL_ROOT,
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
        'aud': jwt_audience,
    }

    try:
        jwt_data = jwt.encode(payload, jwt_secret_key)
        api_client = EdxRestApiClient(api_url, jwt=jwt_data, **kwargs)
    except Exception:  # pylint: disable=broad-except
        log.exception("Failed to initialize the API client with url '%s'.", api_url)
        return

    return api_client


def _make_hash(key):
    """
    Returns the string based on a the hash of the provided key.
    """
    return hashlib.md5(key).hexdigest()
