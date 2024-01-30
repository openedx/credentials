"""
Issuance utils.
"""

import didkit
from asgiref.sync import async_to_sync

# pylint: disable=cyclic-import
from django.utils.translation import gettext as _

from credentials.apps.credentials.models import UserCredential

from ..settings import VerifiableCredentialsImproperlyConfigured
from .models import IssuanceConfiguration, IssuanceLine


def create_issuers():
    """
    Initiate issuers.
    """
    return IssuanceConfiguration.create_issuers()


def get_active_issuers():
    """
    Collect all enabled issuers' ids.
    """
    # currently, the only (system level, default) is supported.
    return list(IssuanceConfiguration.objects.filter(enabled=True).values_list("issuer_id", flat=True))


def get_issuers():
    """
    Collect all issuers.
    """
    # currently, the only (system level, default) is supported.
    return list(IssuanceConfiguration.objects.values())


def get_issuer_ids():
    """
    Collect all issuers' ids.
    """
    # currently, the only (system level, default) is supported.
    return list(IssuanceConfiguration.objects.values_list("issuer_id", flat=True))


def get_default_issuer():
    """
    Fetch the default issuer.
    """
    issuer = IssuanceConfiguration.objects.filter(enabled=True).last()
    if not issuer:
        msg = _("There are no enabled Issuance Configurations for some reason! At least one must be always active.")
        raise VerifiableCredentialsImproperlyConfigured(msg)
    return issuer


def get_issuer(issuer_id):
    """
    Fetch issuer by given ID.
    """
    issuer = IssuanceConfiguration.objects.filter(issuer_id=issuer_id).first()
    return issuer


def get_revoked_indices(issuer_id):
    """
    Collect status indicies for verifiable credentials with revoked achievements (in given Issuer context).
    """
    return IssuanceLine.get_indicies_for_status(issuer_id=issuer_id, status=UserCredential.REVOKED)


@async_to_sync
async def didkit_issue_credential(credential, options, issuer_key):
    """
    Given a credential JSON-LD add validate it and add a proof.
    """
    return await didkit.issue_credential(
        credential, options, issuer_key
    )  # pylint: disable=no-member, useless-suppression


@async_to_sync
async def didkit_verify_credential(credential, proof_options):
    """
    Given a verifiable credential JSON-LD validate/verify it.
    """
    return await didkit.verify_credential(credential, proof_options)  # pylint: disable=no-member, useless-suppression


@async_to_sync
async def didkit_verify_presentation(presentation, proof_options):
    """
    Given a verifiable presentation JSON-LD validate/verify it.
    """
    return await didkit.verify_presentation(
        presentation, proof_options
    )  # pylint: disable=no-member, useless-suppression


@async_to_sync
async def didkit_generate_ed25519_key():
    """
    Generate a Ed25519 keypair and output it in JWK format.

    See: https://www.spruceid.dev/didkit/didkit-packages/command-line-interface#generate-ed25519-key
    """
    return await didkit.generate_ed25519_key()  # pylint: disable=no-member, useless-suppression


async def didkit_key_to_did(*, jwk, method_pattern="key"):
    """
    Generate decentralized identifier fot the given key (JWK).

    See: https://www.spruceid.dev/didkit/didkit-packages/command-line-interface#key-to-did
    """
    return await didkit.key_to_did(
        jwk=jwk, method_pattern=method_pattern
    )  # pylint: disable=no-member, useless-suppression
