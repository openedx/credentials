""" Issuer classes used to generate user credentials."""
from __future__ import unicode_literals

import abc
import logging

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from credentials.apps.api.exceptions import DuplicateAttributeError

from credentials.apps.credentials.models import (
    ProgramCertificate,
    UserCredentialAttribute, UserCredential
)
from credentials.apps.credentials.utils import validate_duplicate_attributes

logger = logging.getLogger(__name__)


class AbstractCredentialIssuer(object):
    """
    Abstract credential issuer.

    Credential issuers are responsible for taking inputs and issuing a single credential (subclass of
    AbstractCredential) to a given user.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def issued_credential_type(self):
        """
        Type of credential type to be issued.

        Returns:
            AbstractCredential
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def issue_credential(self, credential, username, attributes=None):
        """
        Issue a credential to the user.

        This action is idempotent. If the user has already earned the credential, a new one WILL NOT be issued. The
        existing credential WILL NOT be modified.

        Arguments:
            credential (AbstractCredential): Type of credential to issue.
            username (str): username of user for which credential required
            attributes (List[dict]): optional list of attributes that should be associated with the issued credential.

        Returns:
            UserCredential
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def set_credential_attributes(self, user_credential, attributes):
        """
        Add attributes to the given UserCredential.

        Arguments:
            user_credential (AbstractCredential): Type of credential to issue.
            attributes (List[dict]): optional list of attributes that should be associated with the issued credential.
        """
        raise NotImplementedError  # pragma: no cover


class ProgramCertificateIssuer(AbstractCredentialIssuer):
    """ Issues ProgramCertificates. """
    issued_credential_type = ProgramCertificate

    @transaction.atomic
    def issue_credential(self, credential, username, attributes=None):
        user_credential, __ = UserCredential.objects.get_or_create(
            username=username,
            credential_content_type=ContentType.objects.get_for_model(credential),
            credential_id=credential.id
        )

        self.set_credential_attributes(user_credential, attributes)

        return user_credential

    def set_credential_attributes(self, user_credential, attributes):
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
