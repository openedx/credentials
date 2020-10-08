""" Issuer classes used to generate user credentials."""
import abc
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from credentials.apps.api.exceptions import DuplicateAttributeError
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    UserCredential,
    UserCredentialAttribute,
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
            self, credential, username,
            status=UserCredentialStatus.AWARDED,
            attributes=None,
            request=None
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
                'status': status,
            },
        )

        self.set_credential_attributes(user_credential, attributes)

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
                user_credential=user_credential,
                name=attr.get('name'),
                defaults={'value': attr.get('value')}
            )


class ProgramCertificateIssuer(AbstractCredentialIssuer):
    """ Issues ProgramCertificates. """
    issued_credential_type = ProgramCertificate

    @transaction.atomic
    def issue_credential(
            self, credential, username,
            status=UserCredentialStatus.AWARDED,
            attributes=None,
            request=None
    ):
        """
        Issue a Program Certificate to the user.

        This function is being overriden to provide functionality for sending
        an updated email to pathway partners

        This action is idempotent. If the user has already earned the
        credential, a new one WILL NOT be issued. The existing credential
        WILL be modified.

        Arguments:
            credential (AbstractCredential): Type of credential to issue.
            username (str): username of user for which credential required
            status (str): status of credential
            attributes (List[dict]): optional list of attributes that should be associated with the issued credential.
            request (HttpRequest): request object to build program record absolute uris

        Returns:
            UserCredential
        """
        user_credential, created = UserCredential.objects.update_or_create(
            username=username,
            credential_content_type=ContentType.objects.get_for_model(credential),
            credential_id=credential.id,
            defaults={
                'status': status,
            },
        )

        # Send an updated email to a pathway org only if the user has previously sent one
        # This function call should be moved into some type of task queue
        # once credentials has that functionality
        site_config = getattr(credential.site, 'siteconfiguration', None)
        # Add a check to see if records_enabled is True for the site associated with
        # the credentials. If records is not enabled, we should not send this email
        if created and site_config and site_config.records_enabled:
            send_updated_emails_for_program(request, username, credential)

        # If this is a new ProgramCertificate and the `SEND_EMAIL_ON_PROGRAM_COMPLETION`
        # feature is enabled then let's send a congratulatory message to the learner
        if created and getattr(settings, 'SEND_EMAIL_ON_PROGRAM_COMPLETION', False):
            send_program_certificate_created_message(username, credential)

        self.set_credential_attributes(user_credential, attributes)

        return user_credential


class CourseCertificateIssuer(AbstractCredentialIssuer):
    """ Issues CourseCertificates. """
    issued_credential_type = CourseCertificate
