"""
Remove issuer configuration by its Issuer ID.
"""

import logging

from django.core.management import BaseCommand

from credentials.apps.verifiable_credentials.issuance.models import IssuanceConfiguration

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Remove Issuance Configuration based on Issuer ID"

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument("issuer_id", type=str, help="Issuer DID")

    def handle(self, *args, **options):
        issuer_id = options.get("issuer_id")
        removed = IssuanceConfiguration.objects.filter(issuer_id=issuer_id).delete()
        print(removed)
