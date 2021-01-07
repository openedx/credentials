import uuid

from django.test import TestCase

from credentials.apps.catalog.api import get_program_details_by_uuid
from credentials.apps.catalog.data import ProgramDetails
from credentials.apps.catalog.tests.factories import ProgramFactory, SiteFactory


class APITests(TestCase):
    """ Tests internal API calls """

    def setUp(self):
        super().setUp()
        self.site = SiteFactory()

    def test_get_program_details(self):
        program_uuid = uuid.uuid4()
        unused_program_uuid = uuid.uuid4()
        program = ProgramFactory.create(uuid=program_uuid, site=self.site)

        details = get_program_details_by_uuid(uuid=program_uuid, site=program.site)
        self.assertIsNotNone(details)
        self.assertIsInstance(details, ProgramDetails)

        details = get_program_details_by_uuid(uuid=unused_program_uuid, site=program.site)
        self.assertIsNone(details)
