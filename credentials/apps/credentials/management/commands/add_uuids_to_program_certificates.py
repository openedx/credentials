import logging

from django.core.management.base import BaseCommand
from slumber.exceptions import HttpNotFoundError

from credentials.apps.credentials.models import ProgramCertificate
from credentials.apps.credentials.utils import get_program

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This management comand is essentially a one-off.  We are adding this as an extra step to
    populate the newly added UUID field in the ProgramCertificate table.  After it has been
    run to do the initial population, it will not need to be run again.
    """
    help = 'Add missing UUIDs to the programCertificate table'

    def get_uuid_from_api(self, program_id):
        """ Return the UUID for the provided program ID """

        # If there is no ID (meaning the program_id is empty), that is a problem,
        # so report it, this likely means there is an issue with the Db
        if program_id is None:
            raise AttributeError('Need an ID')

        # Now, get the program id.
        item = get_program(program_id)

        return item['uuid']

    def handle(self, *args, **options):
        """ Add missing UUIDs to the programCertificate table"""

        program_certificate_table = ProgramCertificate.objects.filter(program_uuid__isnull=True)

        for program_entry in program_certificate_table:
            try:
                logger.info('Getting UUID for %s', program_entry.program_id)
                program_entry.program_uuid = self.get_uuid_from_api(program_entry.program_id)

                program_entry.save()
            except HttpNotFoundError:
                logger.warning('ID not found: %s', program_entry.program_id)
            except AttributeError:
                logger.warning('Bad ID: %s', program_entry.program_id, exc_info=True)
            except Exception:  # pylint: disable=broad-except
                logger.exception('Error detected trying to get the ID (%s) from the program service',
                                 program_entry.program_id)
