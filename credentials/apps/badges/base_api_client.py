import logging
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from requests.exceptions import HTTPError

from .exceptions import BadgeProviderError


logger = logging.getLogger(__name__)


class BaseBadgeProviderClient(ABC):
    """
    Base class for interacting with a generic badge provider API.

    This class provides common functionality such as performing requests
    and error handling. Methods specific to badge providers must be implemented
    by subclasses.
    """

    PROVIDER_NAME = None
    REQUESTS_TIMEOUT = 10

    def __init__(self):
        self.base_api_url = None

    def perform_request(self, method, url_suffix, data=None):
        """
        Perform an HTTP request to the specified URL suffix.

        Args:
            method (str): HTTP method to use for the request.
            url_suffix (str): URL suffix to append to the base Credly API URL.
            data (dict, optional): Data to send with the request.

        Returns:
            dict: JSON response from the API.

        Raises:
            requests.HTTPError: If the API returns an error response.
        """
        url = urljoin(self.base_api_url, url_suffix)
        logger.debug(f"{self.PROVIDER_NAME} API: {method.upper()} {url}")
        response = requests.request(
            method.upper(), url, headers=self._get_headers(), json=data, timeout=self.REQUESTS_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def _raise_for_error(self, response):
        """
        Raises a CredlyAPIError if the response status code indicates an error.

        Args:
            response (requests.Response): Response object from the Credly API request.

        Raises:
            CredlyAPIError: If the response status code indicates an error.
        """
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error(
                f"Error while processing {self.PROVIDER_NAME} request: {response.status_code} - {response.text}"
            )
            raise BadgeProviderError(f"{response.text} Status({response.status_code})")

    @property
    def base_api_url(self):
        return self._get_base_api_url()

    @abstractmethod
    def _get_headers(self):
        """
        Returns the headers for making API requests.
        """

    @abstractmethod
    def _get_base_api_url(self):
        """
        Returns the base URL for the badge provider API.
        """

    @abstractmethod
    def issue_badge(self, issue_badge_data):
        """
        Issues a badge using the badge provider API.

        Args:
            issue_badge_data (dict): Data required to issue the badge.
        """

    @abstractmethod
    def revoke_badge(self, badge_id, data=None):
        """
        Revoke a badge with the given badge ID.

        Must be implemented by subclasses.

        Args:
            badge_id (str): ID of the badge to revoke.
            data (dict): Additional data for the revocation.
        """
