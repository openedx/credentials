"""
Signal receivers for the `credentials` Django app.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from openedx_events.event_bus import get_producer
from openedx_events.learning.data import CertificateData
from openedx_events.learning.signals import (
    CERTIFICATE_CREATED,
    PROGRAM_CERTIFICATE_AWARDED,
    PROGRAM_CERTIFICATE_REVOKED,
)

from credentials.apps.core.api import get_or_create_user_from_event_data
from credentials.apps.credentials.api import award_course_certificate


User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(CERTIFICATE_CREATED)
def award_certificate_from_event(sender, **kwargs):  # pylint: disable=unused-argument
    """
    When we get a signal indicating that a certificate was created in the LMS, make sure to award a course certificate
    UserCredential to the user in Credentials as well.

    Args:
        kwargs: event data sent with signal
    """
    certificate_data = kwargs.get("certificate", None)
    if not certificate_data or not isinstance(certificate_data, CertificateData):
        logger.error("Received null or unexpected data type from CERTIFICATE_CREATED signal")
        return

    course_event_data = certificate_data.course
    user_event_data = certificate_data.user

    user, __ = get_or_create_user_from_event_data(user_event_data)
    if user:
        logger.info(f"Awarding a course certificate to user [{user.id}] in course run [{course_event_data.course_key}]")
        award_course_certificate(user, str(course_event_data.course_key), certificate_data.mode)
    else:
        logger.error(
            f"Failed to award a course certificate to user with (LMS) user id [{user_event_data.id}] in course run "
            f"[{course_event_data.course_key}]. Could not retrieve or create a user in Credentials associated with the "
            "given user"
        )
        return


@receiver(PROGRAM_CERTIFICATE_AWARDED)
def listen_for_program_certificate_awarded_event(sender, signal, **kwargs):  # pylint: disable=unused-argument
    """
    Receiver for `PROGRAM_CERTIFICATE_AWARDED` events. This function is responsible for extracting required information
    and passing it to another utility function responsible for publishing program certificate events to the event bus.
    """
    _publish_program_certificate_event(PROGRAM_CERTIFICATE_AWARDED, kwargs["program_certificate"], kwargs["metadata"])


@receiver(PROGRAM_CERTIFICATE_REVOKED)
def listen_for_program_certificate_revoked_event(sender, signal, **kwargs):  # pylint: disable=unused-argument
    """
    Receiver for `PROGRAM_CERTIFICATE_REVOKED` events. This function is responsible for extracting required information
    and passing it to another utility function responsible for publishing program certificate events to the event bus.
    """
    _publish_program_certificate_event(PROGRAM_CERTIFICATE_REVOKED, kwargs["program_certificate"], kwargs["metadata"])


def _publish_program_certificate_event(program_certificate_event_type, event_data, event_metadata):
    """
    Publishes Program Certificate lifecycle events to the event bus.

    Args:
        program_certificate_event_type (OpenEdxPublicSignal): The type of event we are publishing to the event bus
         (e.g. PROGRAM_CERTIFICATE_AWARDED or PROGRAM_CERTIFICATE_REVOKED)
        event_data (dict): Learner and credential data extracted from the event signal
        event_metadata (dict): Event metadata extracted from the event signal
    """
    get_producer().send(
        signal=program_certificate_event_type,
        topic=getattr(settings, "PROGRAM_CERTIFICATE_EVENTS_KAFKA_TOPIC_NAME", ""),
        event_key_field="program_certificate.program.uuid",
        event_data={"program_certificate": event_data},
        event_metadata=event_metadata,
    )
