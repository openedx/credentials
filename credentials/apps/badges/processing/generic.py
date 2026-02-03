"""
Main processing logic.
"""

import logging

from credentials.apps.badges.exceptions import BadgesProcessingError
from credentials.apps.badges.processing.progression import process_requirements
from credentials.apps.badges.processing.regression import process_penalties
from credentials.apps.badges.utils import extract_payload, get_user_data
from credentials.apps.core.api import get_or_create_user_from_event_data

logger = logging.getLogger(__name__)


def process_event(sender, **kwargs):
    """
    Badge templates configuration interpreter.

    Responsibilities:
        - identifies a target User based on event's payload ("whose action");
        - runs badges progressive pipeline (requirements processing);
        - runs badges regressive pipeline (penalties processing);
    """

    event_type = sender.event_type

    try:
        # user identification
        username = identify_user(event_type=event_type, event_payload=extract_payload(kwargs))

        # requirements processing
        process_requirements(event_type, username, extract_payload(kwargs))

        # penalties processing
        process_penalties(event_type, username, extract_payload(kwargs))

    except BadgesProcessingError as error:
        logger.error(f"Badges processing error: {error}")
        return None
    return None


def identify_user(*, event_type, event_payload):
    """
    Identifies event user based on provided keyword arguments and returns the username.

    This function extracts user data from the given event's keyword arguments, attempts to identify existing user
    or creates a new user based on this data, and then returns the username.

    Args:
        event_type (str): The type of the event.
        event_payload (dict): The payload of the event.

    Returns:
        str: The username of the identified (and created if needed) user.

    Raises:
        BadgesProcessingError: if user data was not found.
    """

    user_data = get_user_data(event_payload)

    if not user_data:
        message = (
            f"User data cannot be found (got: {user_data}): {event_payload}. "
            f"Does event {event_type} include user data at all?"
        )
        raise BadgesProcessingError(message)

    user, __ = get_or_create_user_from_event_data(user_data)
    return user.username
