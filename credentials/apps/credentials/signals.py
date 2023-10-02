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
    CERTIFICATE_REVOKED,
    PROGRAM_CERTIFICATE_AWARDED,
    PROGRAM_CERTIFICATE_REVOKED,
)

from credentials.apps.core.api import get_or_create_user_from_event_data
from credentials.apps.credentials.api import process_course_credential_update
from credentials.apps.credentials.constants import UserCredentialStatus


User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(CERTIFICATE_CREATED)
@receiver(CERTIFICATE_REVOKED)
def process_course_credential_event(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver for course certificate events consumed from the Event Bus. Depending on the type of event consumed,
    we will then try to award a credential to (or revoke a credential from) a learner. If the learner doesn't exist in
    Credentials yet, we will try to create a User instance for them so we don't lose the update (and this tracks with
    the legacy behavior).
    """
    certificate_data = kwargs.get("certificate", None)
    if not certificate_data or not isinstance(certificate_data, CertificateData):
        logger.error(
            "Unable to process course credential event from the Event Bus, the system received a null or unexpected "
            "CertificateData object."
        )
        return

    event_type = kwargs["signal"].event_type
    user, __ = get_or_create_user_from_event_data(certificate_data.user)
    if user:
        course_run_key = str(certificate_data.course.course_key)
        mode = certificate_data.mode
        if event_type == CERTIFICATE_CREATED.event_type:
            logger.info(f"Awarding a course certificate to user [{user.id}] in course run [{course_run_key}]")
            process_course_credential_update(user, course_run_key, mode, UserCredentialStatus.AWARDED)
        elif event_type == CERTIFICATE_REVOKED.event_type:
            logger.info(f"Revoking a course certificate from user [{user.id}] in course run [{course_run_key}]")
            process_course_credential_update(user, course_run_key, mode, UserCredentialStatus.REVOKED)
    else:
        logger.error(
            f"Unable to process the `{event_type}` event with UUID {kwargs['metadata'].id}: could not retrieve or "
            f"create a user with LMS user id [{certificate_data.user.id}]"
        )


@receiver(PROGRAM_CERTIFICATE_AWARDED)
@receiver(PROGRAM_CERTIFICATE_REVOKED)
def listen_for_program_certificate_events(sender, signal, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver for program certificate events that need to be published to the Event Bus.
    """
    program_credential_event_type = None
    if signal.event_type == PROGRAM_CERTIFICATE_AWARDED.event_type:
        program_credential_event_type = PROGRAM_CERTIFICATE_AWARDED
    elif signal.event_type == PROGRAM_CERTIFICATE_REVOKED.event_type:
        program_credential_event_type = PROGRAM_CERTIFICATE_REVOKED

    if program_credential_event_type:
        get_producer().send(
            signal=program_credential_event_type,
            topic=getattr(settings, "PROGRAM_CERTIFICATE_EVENTS_KAFKA_TOPIC_NAME", ""),
            event_key_field="program_certificate.program.uuid",
            event_data={"program_certificate": kwargs["program_certificate"]},
            event_metadata=kwargs["metadata"],
        )
