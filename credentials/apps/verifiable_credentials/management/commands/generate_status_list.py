"""Generate status list."""

import json
import logging

from django.core.management import BaseCommand

from credentials.apps.verifiable_credentials.issuance.status_list import issue_status_list

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate Status List 2021 verifiable credential"

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument("issuer_id", type=str, help="The issuer DID")

    def handle(self, *args, **options):
        issuer_id = options.get("issuer_id")
        print(json.dumps(issue_status_list(issuer_id), indent=4))
