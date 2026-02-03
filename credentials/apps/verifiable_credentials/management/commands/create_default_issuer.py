"""
Create initial issuers set (based on deployment configuration).
"""

import logging

from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from credentials.apps.verifiable_credentials.issuance.utils import create_issuers
from credentials.apps.verifiable_credentials.toggles import (
    ENABLE_VERIFIABLE_CREDENTIALS,
    is_verifiable_credentials_enabled,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create initial Issuance Configuration(s) based on deployment issuer(s) setup"

    def handle(self, *args, **options):
        if not is_verifiable_credentials_enabled():
            logger.error(
                _("Verifiable Credentials feature is not enabled [{feature_name}]").format(
                    feature_name=ENABLE_VERIFIABLE_CREDENTIALS.name
                )
            )
            return

        create_issuers()
