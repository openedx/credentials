"""
Signal receivers for the `credentials` Django app.
"""
import logging

from django.contrib.auth import get_user_model
from django.dispatch import receiver
from openedx_events.learning.data import CertificateData
from openedx_events.learning.signals import CERTIFICATE_CREATED

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
