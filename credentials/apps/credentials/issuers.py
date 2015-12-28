""" Issuer classes used to generate user credentials."""
from __future__ import unicode_literals

import abc
import logging

from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from credentials.apps.credentials.models import (
    ProgramCertificate,
    UserCredentialAttribute, UserCredential
)

logger = logging.getLogger(__name__)


class AbstractCredentialIssuer(object):
    """
    Abstract credential issuer.

    Credential issuers are responsible for taking inputs and issuing a single credential (subclass of
    ``AbstractCredential``) to a given user.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def issued_credential_type(self):
        """
        Type of credential issued by

        Returns:
            AbstractCredential
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    def issue_credential(self, **kwargs):
        """
        Issue a credential to the user.

        This action is idempotent. If the user has already earned the credential, a new one WILL NOT be issued. The
        existing credential WILL NOT be modified.

        Arguments:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            ``UserCredential``
        """
        raise NotImplementedError  # pragma: no cover


class ProgramCertificateIssuer(AbstractCredentialIssuer):
    """ Issues ProgramCertificates. """
    issued_credential_type = ProgramCertificate

    @transaction.atomic
    def issue_credential(self, username, **kwargs):
        program_id = kwargs['program_id']
        attributes = kwargs['attributes']

        program_certificate = ProgramCertificate.objects.get(program_id=program_id)

        user_credential, created = UserCredential.objects.get_or_create(
            username=username,
            credential_content_type=ContentType.objects.get_for_model(ProgramCertificate),
            credential_id=program_certificate.id
        )

        # if new record created then add its attributes.
        if created:
            attr_list = []
            for attr in attributes:
                if attr.get('namespace') and attr.get('name') and attr.get('value'):
                    attr_list.append(
                        UserCredentialAttribute(
                            user_credential=user_credential,
                            namespace=attr.get('namespace'),
                            name=attr.get('name'),
                            value=attr.get('value')
                        )
                    )

            UserCredentialAttribute.objects.bulk_create(attr_list)
        # if credential already exists then don't create the record.
        else:
            logger.warning("User [%s] already has a credential for program [%s].", username, program_id)
        return user_credential
