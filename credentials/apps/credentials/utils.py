"""
Helper methods for credential app.
"""
import datetime
import logging
from itertools import groupby
from urlparse import urljoin

import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient


log = logging.getLogger(__name__)
PROGRAMS_CACHE_KEY = 'programs.api.data'
ORGANIZATIONS_CACHE_KEY = 'organizations.api.data'


def validate_duplicate_attributes(attributes):
    """
    Validate the attributes data

    Arguments:
        attributes (list): List of dicts contains attributes data

    Returns:
        Boolean: Return True only if data has no duplicated namespace and name

    """
    def keyfunc(attribute):  # pylint: disable=missing-docstring
        return attribute['namespace'], attribute['name']

    sorted_data = sorted(attributes, key=keyfunc)
    for __, group in groupby(sorted_data, key=keyfunc):
        if len(list(group)) > 1:
            return False
    return True


def get_programs():
    """ Get active programs from the Programs service on behalf of the
    credentials service user present in the Programs service.

    Returned value is cached to avoid calling programs service each time a
    certificate is viewed.

    Returns:
        list of dict, representing programs returned by the Programs service.
    """
    no_programs = []

    # Bypass caching if the programs cache ttl is not set.
    use_cache = False
    if settings.PROGRAMS_CACHE_TTL > 0:
        use_cache = True

    if use_cache:
        cached = cache.get(PROGRAMS_CACHE_KEY)
        if cached is not None:
            return cached

    programs_api = get_program_api_client()
    if programs_api is None:
        return no_programs

    try:
        response = programs_api.programs.get()
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to retrieve programs from the Programs API.')
        return no_programs

    results = response.get('results', no_programs)

    if use_cache:
        cache.set(PROGRAMS_CACHE_KEY, results, settings.PROGRAMS_CACHE_TTL)

    return results


def get_organization(organization_key):
    """ Get the organization from the edx-platform on behalf of the
    credentials service user present in the edx-platform system.

    Returned value is cached to avoid calling LMS each time a certificate is
    viewed.

    Arguments:
        organization_key (str): Unique key of the organization for retrieval

    Returns:
        dict, representing organization data returned by the LMS.
    """
    no_organization = {}

    # Bypass caching if the programs cache ttl is not set.
    use_cache = False
    if settings.ORGANIZATIONS_CACHE_TTL > 0:
        use_cache = True

    if use_cache:
        cached = cache.get(ORGANIZATIONS_CACHE_KEY)
        if cached is not None:
            return cached.get(organization_key)

    organizations_api = get_organizations_api_client()
    if organizations_api is None:
        return no_organization

    try:
        response = organizations_api.organization(organization_key).get()
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to retrieve organization with key %s from the Organization API.' % organization_key)
        return no_organization

    if use_cache:
        # update existing cache value with new organization data and save it
        cached.update(response)
        cache.set(ORGANIZATIONS_CACHE_KEY, cached, settings.ORGANIZATIONS_CACHE_TTL)

    return response
    

def get_program_api_url():
    """
    Return absolute url of the programs service api.
    """
    return urljoin(settings.PROGRAMS_URL_ROOT, settings.PROGRAMS_API_URL)


def get_organizations_api_url():
    """
    Return absolute url of the organizations service api.
    """
    return urljoin(settings.LMS_URL_ROOT, settings.ORGANIZATIONS_API_URL)


def get_program_api_client():
    """
    Return api client to communicate with the programs service by using the
    credentials service user in the programs service.
    """
    programs_api_url = get_program_api_url()
    service_username = getattr(settings, 'PROGRAMS_SERVICE_USER', '')
    return _get_service_user_api_client(programs_api_url, service_username)


def get_organizations_api_client():
    """
    Return api client to communicate with the Organizations API by using the
    credentials service user in the LMS.
    """
    organizations_api_url = get_organizations_api_url()
    return _get_lms_service_user_api_client(organizations_api_url)


def _get_service_user_api_client(api_url, service_username):
    """
    Helper method to get edx rest api client for the provided service user
    which is present on the system from 'api_url'.

    Arguments:
        api_url (str): Absolute url of the api
        service_username (str): Username of the service user

    """
    now = datetime.datetime.utcnow()
    expires_in = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)
    payload = {
        'preferred_username': service_username,
        'iss': settings.JWT_AUTH.get('JWT_ISSUER'),
        'exp': now + datetime.timedelta(seconds=expires_in),
        'iat': now,
        'aud': settings.JWT_AUTH.get('JWT_AUDIENCE', ''),
    }

    try:
        jwt_data = jwt.encode(payload, settings.JWT_AUTH.get('JWT_SECRET_KEY'))
        api_client = EdxRestApiClient(api_url, jwt=jwt_data)
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to initialize the Programs API client.')
        return

    return api_client


def _get_lms_service_user_api_client(api_url):
    """
    Helper method to get edx rest api client for the credentials service user
    which is present on the LMS.

    Arguments:
        api_url (str): Absolute url of the api

    """
    try:
        api_client = EdxRestApiClient(
            get_organizations_api_url(),
            oauth_access_token=settings.CREDENTIALS_OAUTH_ACCESS_TOKEN
        )
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to initialize the LMS API client.')
        return

    return api_client
