"""Tests for catalog utilities."""

from unittest.mock import MagicMock

from django.test import TestCase

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program
from credentials.apps.catalog.utils import CatalogDataSynchronizer
from credentials.apps.core.tests.factories import SiteFactory
from credentials.shared.constants import PathwayType


class SynchronizerTests(TestCase):
    """Tests CatalogDataSynchronizer"""

    FIRST_ORG = {
        "uuid": "11111111-2222-4444-9999-111111111111",
        "key": "firstorg",
        "name": "First Org Name",
        "certificate_logo_image_url": "http://www.example.com/image.jpg",
    }

    FIRST_COURSE_RUN = {
        "uuid": "33333333-2222-4444-9999-111111111111",
        "key": "firstcourserun",
        "title": "First Course Run",
        "start_date": "2018-01-01T00:00:00Z",
        "end_date": "2018-06-01T00:00:00Z",
    }

    FIRST_COURSE = {
        "uuid": "22222222-2222-4444-9999-111111111111",
        "key": "coursekey",
        "title": "First Course Title",
        "owners": [FIRST_ORG],
        "course_runs": [FIRST_COURSE_RUN],
    }

    FIRST_PROGRAM = {
        "uuid": "44444444-2222-4444-9999-111111111111",
        "title": "First Program Title",
        "authoring_organizations": [FIRST_ORG],
        "courses": [FIRST_COURSE],
        "type": "FancyProgram",
        "status": "active",
        "type_attrs": {"slug": "fancyprogram"},
        "total_hours_of_effort": 4,
    }

    FIRST_PATHWAY = {
        "uuid": "55555555-2222-4444-9999-111111111111",
        "name": "First Pathway",
        "org_name": "First Org Name",
        "email": "test@example.com",
        "status": "published",
        "programs": [FIRST_PROGRAM],
        "pathway_type": PathwayType.INDUSTRY.value,
    }  # Check type is industry since type defaults to credit

    # To test additions, updates, and deletions we're:
    # - Adding of new course run, and adding it to the program
    # - Changing the course name
    # - Excluding the first course run from the program
    # - Deleting the pathway

    SECOND_COURSE_RUN = {
        "uuid": "33333333-2222-4444-9999-222222222222",
        "key": "secondcourserun",
        "title": "Second Course Run",
        "start_date": "2018-01-01T00:00:00Z",
        "end_date": "2018-06-01T00:00:00Z",
    }
    UPDATED_COURSE = dict(
        FIRST_COURSE, **{"title": "Updated Course Title", "course_runs": [FIRST_COURSE_RUN, SECOND_COURSE_RUN]}
    )
    # Used to emulate excluded course runs on programs
    PROGRAM_SPECIFIC_UPDATED_COURSE = dict(UPDATED_COURSE, **{"course_runs": [SECOND_COURSE_RUN]})
    UPDATED_PROGRAM = dict(FIRST_PROGRAM, **{"courses": [PROGRAM_SPECIFIC_UPDATED_COURSE]})
    UPDATED_PATHWAY = {}

    # Each item is a single resource (e.g. a program not a list of programs) because that's what the parse_method takes
    API_RESPONSES = [
        {
            "organizations": FIRST_ORG,
            "courses": FIRST_COURSE,
            "programs": FIRST_PROGRAM,
            "pathways": FIRST_PATHWAY,
        },
        {
            "organizations": FIRST_ORG,
            "courses": UPDATED_COURSE,
            "programs": UPDATED_PROGRAM,
            "pathways": None,
        },
    ]

    def setUp(self):
        super().setUp()
        self.site = SiteFactory()
        # Indexes into API_RESPONSES
        self.api_call_count = 0

    def _mock_fetch_resource(
        self, resource_name, parse_method, extra_request_params=None
    ):  # pylint: disable=unused-argument
        data = self.API_RESPONSES[self.api_call_count].get(resource_name)
        if data:
            parse_method(data)

    def assert_no_data(self):
        assert Course.objects.all().count() == 0
        assert CourseRun.objects.all().count() == 0
        assert Organization.objects.all().count() == 0
        assert Program.objects.all().count() == 0
        assert Pathway.objects.all().count() == 0

    def test_fetch_data_create(self):
        """
        Tests that data is created on `fetch_data`.

        Checks
            - program, course, course run, pathway, and organization are created
        """
        self.assert_no_data()
        synchronizer = CatalogDataSynchronizer(self.site, None, "")
        synchronizer.fetch_resource = self._mock_fetch_resource
        self.api_call_count = 0
        synchronizer.fetch_data()

        # Check organization
        organization = Organization.objects.all().first()
        assert str(organization.uuid) == self.FIRST_ORG["uuid"]

        # Check course run
        course_run = CourseRun.objects.all().first()
        assert str(course_run.uuid) == self.FIRST_COURSE_RUN["uuid"]

        # Check course
        course = Course.objects.all().first()
        assert str(course.uuid) == self.FIRST_COURSE["uuid"]
        assert list(course.owners.all()) == [organization]
        assert list(course.course_runs.all()) == [course_run]

        # Check program
        program = Program.objects.all().first()
        assert str(program.uuid) == self.FIRST_PROGRAM["uuid"]
        assert list(program.authoring_organizations.all()) == [organization]
        assert list(program.course_runs.all()) == [course_run]
        assert program.title == self.FIRST_PROGRAM["title"]

        # Check pathway
        pathway = Pathway.objects.all().first()
        assert str(pathway.uuid) == self.FIRST_PATHWAY["uuid"]
        assert pathway.status == self.FIRST_PATHWAY["status"]
        assert list(pathway.programs.all()) == [program]

    def test_fetch_data_update(self):
        """
        Tests that data is updated on `fetch_data`

        Checks:
            - existing program, course, pathway, and organization exist
            - existing program changed name
            - new course run exists and is attached to course
            - existing course run still exists, but isn't attached to course

        NOTE: This is the state the database will be in between calls without `--delete` and a call with `--delete``
        """

        self.assert_no_data()
        synchronizer = CatalogDataSynchronizer(self.site, None, "")
        synchronizer.fetch_resource = self._mock_fetch_resource
        self.api_call_count = 0
        synchronizer.fetch_data()

        # test_fetch_data_create already tests all code above
        # get updated API data
        self.api_call_count = 1
        synchronizer.fetch_data()

        # Check organization is still the same
        organization = Organization.objects.all().first()
        assert str(organization.uuid) == self.FIRST_ORG["uuid"]

        # Check old course run wasn't deleted, and new one is created
        original_course_run = CourseRun.objects.all()[0]
        new_course_run = CourseRun.objects.all()[1]
        assert str(original_course_run.uuid) == self.FIRST_COURSE_RUN["uuid"]
        assert str(new_course_run.uuid) == self.SECOND_COURSE_RUN["uuid"]

        # Check course still exists and both course runs
        course = Course.objects.all().first()
        assert str(course.uuid) == self.UPDATED_COURSE["uuid"]
        assert list(course.owners.all()) == [organization]
        assert list(course.course_runs.all()) == [original_course_run, new_course_run]

        # Check program still exists, name is changed, and contains both course runs
        program = Program.objects.all().first()
        assert str(program.uuid) == self.UPDATED_PROGRAM["uuid"]
        assert list(program.authoring_organizations.all()) == [organization]
        assert list(program.course_runs.all()) == [new_course_run]
        assert program.title == self.UPDATED_PROGRAM["title"]

        # Check pathway still exists and has updated program
        pathway = Pathway.objects.all().first()
        assert str(pathway.uuid) == self.FIRST_PATHWAY["uuid"]
        assert pathway.status == self.FIRST_PATHWAY["status"]
        assert list(pathway.programs.all()) == [program]

    def test_remove_obsolete_data(self):
        """
        Test that data is delete when `remove_obsolete_data is ran`

        Checks:
            - existing program, course, pathway, and organization exist
            - existing program changed name
            - new course run exists and is attached to course
            - existing course run is deleted

        NOTE: The tests above will check for creation and updates, so this test only checks for deletions
        """
        # Call the API twice to
        self.assert_no_data()
        synchronizer = CatalogDataSynchronizer(self.site, None, "")
        synchronizer.fetch_resource = self._mock_fetch_resource

        self.api_call_count = 0
        synchronizer.fetch_data()

        # Create new synchronizer, imitating new management command call
        synchronizer = CatalogDataSynchronizer(self.site, None, "")
        synchronizer.fetch_resource = self._mock_fetch_resource

        self.api_call_count = 1
        synchronizer.fetch_data()

        # Pathway still exists even though the second API call removed it
        assert Pathway.objects.all().count() == 1

        # Store counts of old models
        org_count = Organization.objects.all().count()
        course_run_count = CourseRun.objects.all().count()
        course_count = Course.objects.all().count()
        program_count = Program.objects.all().count()

        # Delete data. Should just delete single pathway
        synchronizer.remove_obsolete_data()

        assert Pathway.objects.all().count() == 0
        assert Organization.objects.all().count() == org_count
        assert CourseRun.objects.all().count() == course_run_count
        assert Course.objects.all().count() == course_count
        assert Program.objects.all().count() == program_count

    def test_fetch_resource(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"results": [self.FIRST_PROGRAM], "next": None})
        mock_api_client = MagicMock()
        mock_api_client.get = MagicMock(return_value=mock_response)

        mock_parse_method = MagicMock()
        synchronizer = CatalogDataSynchronizer(self.site, mock_api_client, "http://example.com/api/v1/")
        synchronizer.fetch_resource("programs", mock_parse_method)

        mock_response.raise_for_status.assert_called_once()
        mock_parse_method.assert_called_with(self.FIRST_PROGRAM)
