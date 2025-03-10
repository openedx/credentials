"""
These signal handlers are auto-subscribed to all expected badging signals (event types).

See:
"""

import logging

from django.dispatch import receiver
from openedx_events.tooling import OpenEdxPublicSignal, load_all_signals

from credentials.apps.badges.issuers import AccredibleBadgeTemplateIssuer, CredlyBadgeTemplateIssuer
from credentials.apps.badges.models import AccredibleGroup, BadgeProgress, CredlyBadgeTemplate
from credentials.apps.badges.processing.generic import process_event
from credentials.apps.badges.signals import (
    BADGE_PROGRESS_COMPLETE,
    BADGE_PROGRESS_INCOMPLETE,
    BADGE_REQUIREMENT_FULFILLED,
    BADGE_REQUIREMENT_REGRESSED,
)
from credentials.apps.badges.utils import get_badging_event_types


logger = logging.getLogger(__name__)


def listen_to_badging_events():
    """
    Subscribes the main processing handler to badging events subset.
    """

    load_all_signals()

    for event_type in get_badging_event_types():
        signal = OpenEdxPublicSignal.get_signal_by_type(event_type)
        signal.connect(handle_badging_event, dispatch_uid=event_type)


def handle_badging_event(sender, signal, **kwargs):  # pylint: disable=unused-argument
    """
    Generic handler for incoming from the Event bus public signals.
    """

    logger.debug(f"BADGES: incoming signal - {signal}")

    process_event(signal, **kwargs)


@receiver(BADGE_REQUIREMENT_FULFILLED)
def handle_requirement_fulfilled(sender, username, **kwargs):
    """
    On user's Badge progression (completion).
    """
    BadgeProgress.for_user(username=username, template_id=sender.template.id).progress()


@receiver(BADGE_REQUIREMENT_REGRESSED)
def handle_requirement_regressed(sender, username, **kwargs):
    """
    On user's Badge regression (incompletion).
    """
    BadgeProgress.for_user(username=username, template_id=sender.template.id).regress()


@receiver(BADGE_PROGRESS_COMPLETE)
def handle_badge_completion(sender, username, badge_template_id, origin, **kwargs):  # pylint: disable=unused-argument
    """
    Handles the completion of all requirements for a badge template.

    Parameters:
    - username (str): The username of the recipient.
    - badge_template_id (str): The ID of the completed badge template.
    - origin (str): The source of the badge template (e.g., credly, accredible).

    Note:
    - Currently, the appropriate issuer class is selected manually based on the `origin` parameter.
    - In the future, this will be replaced with a more extensible implementation that supports
        additional issuers via plugins.
    """

    logger.debug("BADGES: progress is complete for %s on the %s", username, badge_template_id)

    if origin == CredlyBadgeTemplate.ORIGIN:
        CredlyBadgeTemplateIssuer().award(username=username, credential_id=badge_template_id)
    elif origin == AccredibleGroup.ORIGIN:
        AccredibleBadgeTemplateIssuer().award(username=username, credential_id=badge_template_id)


@receiver(BADGE_PROGRESS_INCOMPLETE)
def handle_badge_regression(sender, username, badge_template_id, origin, **kwargs):  # pylint: disable=unused-argument
    """
    On user's Badge regression (incompletion).

    - username
    - badge template ID
    """

    if origin == CredlyBadgeTemplate.ORIGIN:
        CredlyBadgeTemplateIssuer().revoke(badge_template_id, username)
    elif origin == AccredibleGroup.ORIGIN:
        AccredibleBadgeTemplateIssuer().revoke(badge_template_id, username)
