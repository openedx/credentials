"""
Issuer classes used to generate credentials for learners.
"""

import abc
import logging
from datetime import timezone
from uuid import uuid4

from analytics.client import Client as SegmentClient
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from openedx_events.learning.data import ProgramCertificateData, ProgramData, UserData, UserPersonalData
from openedx_events.learning.signals import PROGRAM_CERTIFICATE_AWARDED, PROGRAM_CERTIFICATE_REVOKED

from credentials.apps.api.exceptions import DuplicateAttributeError
from credentials.apps.core.api import get_user_by_username
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    UserCredential,
    UserCredentialAttribute,
    UserCredentialDateOverride,
)
from credentials.apps.credentials.utils import send_program_certificate_created_message, validate_duplicate_attributes
from credentials.apps.records.utils import send_updated_emails_for_program


logger = logging.getLogger(__name__)


class AbstractCredentialIssuer(metaclass=abc.ABCMeta):
    """
    Abstract credential issuer.

    Credential issuers are responsible for taking inputs and issuing a single credential (subclass of
    AbstractCredential) to a given user.
    """

    @property
    @abc.abstractmethod
    def issued_credential_type(self):
        """
        Type of credential type to be issued.

        Returns:
            AbstractCredential
        """
        raise NotImplementedError  # pragma: no cover

    @transaction.atomic
    def issue_credential(
        self,
        credential,
        username,
        status=UserCredentialStatus.AWARDED,
        attributes=None,
        date_override=None,
        request=None,
        lms_user_id=None,  # pylint: disable=unused-argument
    ):
        """
        Issue a credential to the user.

        This action is idempotent. If the user has already earned the credential, a new one WILL NOT be issued. The
        existing credential WILL be modified.

        Arguments:
            credential (AbstractCredential): Type of credential to issue.
            username (str): username of user for which credential required
            status (str): status of credential
            attributes (List[dict]): optional list of attributes that should be associated with the issued credential.
            request (HttpRequest): request object to build program record absolute uris

        Returns:
            UserCredential
        """
        user_credential, __ = UserCredential.objects.update_or_create(
            username=username,
            credential_content_type=ContentType.objects.get_for_model(credential),
            credential_id=credential.id,
            defaults={
                "status": status,
            },
        )

        self.set_credential_attributes(user_credential, attributes)
        self.set_credential_date_override(user_credential, date_override)

        return user_credential

    @transaction.atomic
    def set_credential_attributes(self, user_credential, attributes):
        """
        Add attributes to the given UserCredential.

        Arguments:
            user_credential (AbstractCredential): Type of credential to issue.
            attributes (List[dict]): optional list of attributes that should be associated with the issued credential.
        """
        if not attributes:
            return

        if not validate_duplicate_attributes(attributes):
            raise DuplicateAttributeError("Attributes cannot be duplicated.")

        for attr in attributes:
            UserCredentialAttribute.objects.update_or_create(
                user_credential=user_credential, name=attr.get("name"), defaults={"value": attr.get("value")}
            )

    @transaction.atomic
    def set_credential_date_override(self, user_credential, date_override=None):
        """
        Add a date override to the given User Credential, or remove it if there should no longer be one.

        Arguments:
            user_credential (AbstractCredential): The credential to associate this date override to
            date_override (Date): The date override that should be associated with this credential
        """

        if date_override and date_override.get("date"):
            UserCredentialDateOverride.objects.update_or_create(
                user_credential=user_credential, defaults={"date": date_override.get("date")}
            )
        else:
            UserCredentialDateOverride.objects.filter(user_credential=user_credential).delete()


class ProgramCertificateIssuer(AbstractCredentialIssuer):
    """
    Issues Program Certificates to learners.
    """

    issued_credential_type = ProgramCertificate

    @transaction.atomic
    def issue_credential(
        self,
        credential,
        username,
        status=UserCredentialStatus.AWARDED,
        attributes=None,
        date_override=None,
        request=None,
        lms_user_id=None,
    ):
        """
        Issues or updates a Program Certificate to a learner.

        This function is overridden to provide additional functionality specific to program certificate generation:
            * If a learner has shared their program progress through a pathway before earning a (program) certificate,
            when the certificate is finally awarded we will automatically attempt to send an updated program record
            email via the pathway.
            * If enabled, when the learner has earned a program certificate, the system will attempt to send a
            congratulations email to the learner (a.k.a a "program completion email").

        This action is idempotent. If the user has already earned the credential, a new one WILL NOT be issued. The
        existing credential WILL be modified.

        Arguments:
            credential (AbstractCredential): The type of credential to issue
            username (str): The username of the learner we are granting a credential to
            status (str): The status of credential (e.g. `awarded`)
            attributes (List[dict]): Optional. List of attributes that should be associated with the issued credential.
            date_override (DateTime): Optional. The date that *should* be displayed (over all others) on a credential.
             Not supported for program certificates.
            request (HttpRequest): The original request object, used to build program record URI
            lms_user_id (int): The learner's LMS User Id, used to send emails to the learner via ACE

        Returns:
            UserCredential
        """
        user_credential, created = UserCredential.objects.update_or_create(
            username=username,
            credential_content_type=ContentType.objects.get_for_model(credential),
            credential_id=credential.id,
            defaults={
                "status": status,
            },
        )

        site_config = getattr(credential.site, "siteconfiguration", None)
        user = get_user_by_username(username)

        # set any additional attributes specific to this program certificate
        self.set_credential_attributes(user_credential, attributes)
        # send an updated program progress message if the learner shared their progress before earning their credential
        self._send_updated_emails_for_program(request, site_config, username, credential, created)
        # send a congratulatory email message to the learner for earning a credential (if program has opted in)
        self._send_program_completion_email(username, credential, created, lms_user_id)
        # emit any program credential events to the event bus
        self._emit_program_certificate_signal(user, user_credential, status, credential)
        # emit a segment event for analytics tracking
        self._emit_program_certificate_segment_event(request, site_config, user, user_credential, credential, created)

        return user_credential

    def _send_updated_emails_for_program(self, request, site_config, username, credential, created):
        """
        This function is responsible for sending an updated email to a pathway org only if the user has previously
        shared their program progress through a pathway. Checks if the site configuration has record keeping enabled
        and, if not, we do not send an email.

        We may want to move this function call to some type of task queue in the future once Credentials supports this
        functionality.

        Args:
            request (HttpRequest): The original HttpRequest object
            username (str): The username of the user associated with the recently generated credential
            credential (AbstractCredential[ProgramCertificate]): The type of credential used to issue the above user
             credential
            created (bool): A boolean describing whether the credential was created (True) or just updated (False)
        """
        if site_config and site_config.records_enabled and created:
            send_updated_emails_for_program(request, username, credential)

    def _send_program_completion_email(self, username, credential, created, lms_user_id):
        """
        This function is responsible for sending a congratulatory message to a learner when a program certificate is
        awarded to them. This feature requires that the `SEND_EMAIL_ON_PROGRAM_COMPLETION` setting is enabled AND that
        the program has opted-in to sending messages upon completion.

        Args:
            username (str): The username of the user associated with the recently generated credential
            credential (AbstractCredential[ProgramCertificate]): The type of credential used to issue the above user
             credential
            created (bool): A boolean describing whether the credential was created (True) or just updated (False)
            lms_user_id (int): The learner's LMS User Id, used to send emails to the learner via ACE
        """
        if created and getattr(settings, "SEND_EMAIL_ON_PROGRAM_COMPLETION", False):
            send_program_certificate_created_message(username, credential, lms_user_id)

    def _emit_program_certificate_signal(self, user, user_credential, status, credential):
        """
        A utility function of the ProgramCertificate issuer responsible for emitting signals when a program certificate
        has been awarded or revoked. This is used to emit signals downstream that are responsible for publishing
        program certificate events to the event bus.

        If neither of the program certificate signals are enabled (through the SEND_PROGRAM_CERTIFICATE_AWARDED_SIGNAL
        and the SEND_PROGRAM_CERTIFICATE_REVOKED_SIGNAL settings) we do nothing.

        Args:
            user (User): The user (learner) associated with the recently generated credential
            user_credential (UserCredential): A UserCredential instance, specifically a program certificate
            credential (AbstractCredential[ProgramCertificate]): The type of credential used to issue the above user
             credential
            date_override (DateTime): A DateTime describing when the learner's credential is available to view
        """
        if not user:
            logger.warning(
                f"Unable to send a program certificate event for user with username [{user_credential.username}]. No "
                "user found matching this username"
            )
            return

        # pull the program and site through the relationship to the Credential
        program = credential.program
        site = credential.site

        program_certificate_data = ProgramCertificateData(
            user=UserData(
                pii=UserPersonalData(username=user.username, email=user.email, name=user.get_full_name()),
                id=user.lms_user_id,
                is_active=user.is_active,
            ),
            program=ProgramData(
                uuid=str(program.uuid),
                title=program.title,
                program_type=program.type_slug,
            ),
            uuid=str(user_credential.uuid),
            status=user_credential.status,
            url=f"https://{site.domain}/credentials/{str(user_credential.uuid).replace('-', '')}/",
        )

        time = user_credential.modified.astimezone(timezone.utc)
        if status == UserCredentialStatus.AWARDED:
            # .. event_implemented_name: PROGRAM_CERTIFICATE_AWARDED
            PROGRAM_CERTIFICATE_AWARDED.send_event(time=time, program_certificate=program_certificate_data)
        elif status == UserCredentialStatus.REVOKED:
            # .. event_implemented_name: PROGRAM_CERTIFICATE_REVOKED
            PROGRAM_CERTIFICATE_REVOKED.send_event(time=time, program_certificate=program_certificate_data)

    def _emit_program_certificate_segment_event(self, request, site_config, user, user_credential, credential, created):
        """
        A utility function used to dispatch a Segment event when a program certificate record has been created or
        updated.

        Args:
            request (HttpRequest): The original request object from the credential update request
            site_config (SiteConfiguration): The site configuration associated with the (program) credential
            user (User): The user (learner) associated with the recently generated credential
            user_credential (UserCredential): The recently generated user credential associated with the learner
            credential (AbstractCredential[ProgramCredential]): The credential issued to the learner, associated with a
             specific program.
            created (bool): Boolean describing if this user credential record was created or updated
        """
        if not user:
            logger.warning(
                f"Unable to send a Segment event for user with username [{user_credential.username}]. No user found "
                "matching this username"
            )
            return

        segment_client = None
        if site_config and site_config.segment_key:
            segment_client = SegmentClient(write_key=site_config.segment_key)

        if segment_client:
            event_name = "edx.bi.credentials.credential_issuers.program_certificate_updated"
            if created:
                event_name = "edx.bi.credentials.credential_issuers.program_certificate_created"

            program = credential.program
            event_properties = {
                "category": "credentials",
                "user": {
                    "username": user.username,
                    "lms_user_id": user.lms_user_id,
                },
                "program": {
                    "uuid": str(program.uuid),
                    "title": program.title,
                    "program_type": program.type_slug,
                },
                "uuid": str(user_credential.uuid),
                "status": user_credential.status,
                "url": f"https://{credential.site.domain}/credentials/{str(user_credential.uuid).replace('-', '')}/",
                "timestamp": user_credential.modified,
            }

            segment_client.track(
                anonymous_id=user.lms_user_id,
                event=event_name,
                properties=event_properties,
            )


class CourseCertificateIssuer(AbstractCredentialIssuer):
    """Issues CourseCertificates."""

    issued_credential_type = CourseCertificate
