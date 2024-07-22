"""
Badge progression processing.
"""

import logging
from typing import List

from attrs import asdict

from credentials.apps.badges.models import BadgeRequirement


logger = logging.getLogger(__name__)


def discover_requirements(event_type: str) -> List[BadgeRequirement]:
    """
    Picks all relevant requirements based on the event type.
    """

    return BadgeRequirement.objects.filter(event_type=event_type, template__is_active=True)


def process_requirements(event_type, username, payload):
    """
    Finds all relevant requirements, tests them one by one, marks as completed if needed.
    """

    requirements = discover_requirements(event_type=event_type)
    completed_templates = set()

    logger.debug("BADGES: found %s requirements to process.", len(requirements))

    for requirement in requirements:

        # remember: the badge template is already "done"
        if requirement.template.is_completed(username):
            completed_templates.add(requirement.template_id)

        # drop early: if the badge template is already "done"
        if requirement.template_id in completed_templates:
            continue

        # drop early: if the requirement is already "done"
        if requirement.is_fulfilled(username):
            continue

        # process: payload rules
        if requirement.apply_rules(asdict(payload)):
            requirement.fulfill(username)
