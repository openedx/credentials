""" Issuer classes used to generate user credentials."""
import abc
import logging

import six
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from credentials.apps.api.exceptions import DuplicateAttributeError
from credentials.apps.credentials.constants import UserCredentialStatus
from credentials.apps.credentials.models import (CourseCertificate, ProgramCertificate, UserCredential,
                                                 UserCredentialAttribute)
from credentials.apps.credentials.utils import validate_duplicate_attributes

logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class AbstractCredentialIssuer(object):
    """
    Abstract credential issuer.

    Credential issuers are responsible for taking inputs and issuing a single credential (subclass of
    AbstractCredential) to a given user.
    """

    @abc.abstractproperty
    def issued_credential_type(self):
        """
        Type of credential type to be issued.

        Returns:
            AbstractCredential
        """
        raise NotImplementedError  # pragma: no cover

    @transaction.atomic
    def issue_credential(self, credential, username, status=UserCredentialStatus.AWARDED, attributes=None):
        """
        Issue a credential to the user.

        This action is idempotent. If the user has already earned the credential, a new one WILL NOT be issued. The
        existing credential WILL be modified.

        Arguments:
            credential (AbstractCredential): Type of credential to issue.
            username (str): username of user for which credential required
            status (str): status of credential
            attributes (List[dict]): optional list of attributes that should be associated with the issued credential.

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


class CourseCertificateIssuer(AbstractCredentialIssuer):
    """ Issues CourseCertificates. """
    issued_credential_type = CourseCertificate
