"""
Badge regression processing.
"""

import logging
from typing import List

from attrs import asdict

from credentials.apps.badges.models import BadgePenalty


logger = logging.getLogger(__name__)


def discover_penalties(event_type: str) -> List[BadgePenalty]:
    """
    Picks all relevant penalties based on the event type.
    """

    return BadgePenalty.objects.filter(event_type=event_type, template__is_active=True)


def process_penalties(event_type, username, payload):
    """
    Finds all relevant penalties, tests them one by one, marks related requirement as not completed if needed.
    """

    penalties = discover_penalties(event_type=event_type)

    logger.debug("BADGES: found %s penalties to process.", len(penalties))

    for penalty in penalties:

        # process: payload rules
        if penalty.apply_rules(asdict(payload)):
            penalty.reset_requirements(username)
