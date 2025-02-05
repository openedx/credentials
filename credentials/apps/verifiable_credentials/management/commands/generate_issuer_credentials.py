"""Generate issuance credentials with didkit."""

import logging
from pprint import pprint

import didkit
from django.core.management import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate private key for Issuer (JWK) and a decentralized identifier (DID) based on that key"

    def handle(self, *args, **options):
        key = didkit.generate_ed25519_key()  # pylint: disable=no-member, useless-suppression
        did = didkit.key_to_did(jwk=key, method_pattern="key")  # pylint: disable=no-member, useless-suppression

        issuer_credentials = {
            "private_key": key,
            "did": did,
        }
        pprint(issuer_credentials)
