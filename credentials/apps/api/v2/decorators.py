"""
Decorators for the API app of Credentials.
"""

import logging

from django.conf import settings


logger = logging.getLogger(__name__)


def log_incoming_request(func):
    """
    A decorator that can be used to log information from an incoming REST request. Please take care if using this
    decorator, we don't want to accidentally log any secrets or sensitive PII.

    Use of this decorator is also gated by the `LOG_INCOMING_REQUESTS` waffle switch. This is to ensure that we can
    toggle this functionality as needed and keep log sizes reasonable.
    """

    def wrapper(*args, **kwargs):
        if settings.LOG_INCOMING_REQUESTS.is_enabled():
            try:
                request = args[1]
                data = request.body
                logger.info(
                    f"{request.method} request received to endpoint [{request.get_full_path()}] from user "
                    f"[{request.user.username}] originating from [{request.headers.get('host', 'Unknown')}] "
                    f"with data: [{data}]"
                )
            except Exception as exc:
                # catch overly broad exception to try to ensure if logging doesn't work the request will still be
                # processed
                logger.error(f"Error logging incoming request: {exc}. Continuing...")

        return func(*args, **kwargs)

    return wrapper
