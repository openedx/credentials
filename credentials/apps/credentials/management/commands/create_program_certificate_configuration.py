"""Management command to create a program certificate configuration for the demo program"""

import logging

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

from credentials.apps.catalog.models import Program
from credentials.apps.credentials.models import ProgramCertificate


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to create a program certificate configuration for the demo program.
    This is meant to be run from a provisioning script for devstack and not by hand.
    """

    def add_arguments(self, parser):
        """Arguments for the command. defaults are the demo program for devstack"""
        parser.add_argument("--domain-name", default="example.com")
        parser.add_argument("--program-name", default="edX Demonstration Program")

    def handle(self, *args, **kwargs):
        site_domain = kwargs.get("domain_name")
        program_name = kwargs.get("program_name")
        try:
            ProgramCertificate.objects.get_or_create(
                site=Site.objects.get(domain=site_domain),
                program_uuid=self.get_example_program_uuid(program_name),
                is_active=True,
            )
        except Exception as e:
            raise CommandError(e)

    def get_example_program_uuid(self, program_name):
        try:
            demo_program = Program.objects.get(title=program_name)
            return demo_program.uuid
        except Program.DoesNotExist:
            raise CommandError("The demo program either doesn't exist or is not yet in the catalogue")
