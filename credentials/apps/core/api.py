"""
Python APIs exposed by the core Django app.
"""

import logging

from django.contrib.auth import get_user_model
from openedx_events.learning.data import UserData


User = get_user_model()
logger = logging.getLogger(__name__)


def get_user_by_username(username):
    """
    Utility function that retrieves a returns a User instance based on a given username. Returns None if a user cannot
    be found with given username.

    Args:
        username (String): The username of the User instance we are trying to retrieve

    Returns:
        The User instance related to the given username, or None if there is no learner associated with the given
        username.
    """
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None


def get_or_create_user_from_event_data(user_data):
    """
    Utility function to retrieve a User instance while processing event bus events. If the user does not exist, we will
    create a new User instance using data from the event the Credentials IDA is currently processing.

    Args:
        user_data (UserData): The learner's data extracted from the event bus event being processed

    Returns:
        user (User): The User instance associated with the learner from the event data
        created (Bool): A boolean describing if the user existed (and was retrieved) or created
    """
    if not user_data or not isinstance(user_data, UserData):
        logger.error("Received null or unexpected data type when attempting to retrieve User information")
        return None, None

    try:
        # create the user if they don't exist, this follows similar behavior that our JWT authentication implements if
        # a user doesn't exist when we're making network calls across services
        user, created = User.objects.get_or_create(username=user_data.pii.username)
    except Exception:
        logger.exception("Error occurred retrieving or creating a user")
        return None, None

    if created:
        logger.info(f"Created new Credentials user with id {user.id}. Updating attributes from event data...")
        user.lms_user_id = user_data.id
        user.is_active = user_data.is_active
        user.full_name = user_data.pii.name
        user.email = user_data.pii.email
        user.save()

    return user, created
