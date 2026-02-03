import uuid
from typing import TYPE_CHECKING, List

from django.test import TestCase

from credentials.apps.catalog.api import (
    get_course_runs_by_course_run_keys,
    get_filtered_programs,
    get_program_details_by_uuid,
)
from credentials.apps.catalog.data import ProgramDetails, ProgramStatus
from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
    SiteFactory,
)
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.tests.factories import CourseCertificateFactory

if TYPE_CHECKING:
    from credentials.apps.credentials.models import CourseCertificate


class APITests(TestCase):
    """Tests internal API calls"""

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


class GetCourseRunsByCourseRunKeysTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.course_certs: List["CourseCertificate"] = [
            CourseCertificateFactory.create(
                course_id=course_run.key,
                site=self.site,
            )
            for course_run in self.course_runs
        ]

    def test_get_course_runs_by_course_run_keys_zero(self):
        course_run_key = []
        result = get_course_runs_by_course_run_keys(course_run_key)
        assert len(result) == 0

    def test_get_course_runs_by_course_run_keys_one(self):
        course_run_key = [self.course_certs[0].course_run.key]
        result = get_course_runs_by_course_run_keys(course_run_key)
        assert result[0] == self.course_runs[0]

    def test_get_course_runs_by_course_run_keys_multiple(self):
        course_run_keys = [course_cert.course_run.key for course_cert in self.course_certs]
        result = get_course_runs_by_course_run_keys(course_run_keys)
        assert result[0] == self.course_runs[0]
        assert result[1] == self.course_runs[1]


class GetFilteredProgramsTests(SiteMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(
            title="TestProgram1", course_runs=self.course_runs, authoring_organizations=self.orgs, site=self.site
        )
        self.program2 = None
        self.program3 = None

    def test_get_filtered_programs_retired_true_empty_true(self):
        self.program2 = ProgramFactory(
            title="TestProgram2Retired",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
            status=ProgramStatus.RETIRED.value,
        )
        self.program3 = ProgramFactory(
            title="TestProgram3Empty", course_runs=None, authoring_organizations=self.orgs, site=self.site
        )
        # include retired and empty programs
        result = get_filtered_programs(self.site, [ProgramStatus.ACTIVE.value, ProgramStatus.RETIRED.value])
        assert len(result) == 3
        assert result[0] == self.program
        assert result[1] == self.program2
        assert result[2] == self.program3

    def test_get_filtered_programs_retired_false_empty_true(self):
        self.program2 = ProgramFactory(
            title="TestProgram2Retired",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
            status=ProgramStatus.RETIRED.value,
        )
        self.program3 = ProgramFactory(
            title="TestProgram3Empty", course_runs=None, authoring_organizations=self.orgs, site=self.site
        )
        # include empty programs
        result = get_filtered_programs(self.site, [ProgramStatus.ACTIVE.value])
        assert len(result) == 2
        assert result[0] == self.program
        assert result[1] == self.program3

    def test_get_filtered_programs_retired_true_empty_false(self):
        self.program2 = ProgramFactory(
            title="TestProgram2Retired",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
            status=ProgramStatus.RETIRED.value,
        )
        self.program3 = ProgramFactory(
            title="TestProgram3Empty", course_runs=None, authoring_organizations=self.orgs, site=self.site
        )
        # include retired programs
        course_filters = {"course_runs__in": self.course_runs}
        result = get_filtered_programs(
            self.site, [ProgramStatus.ACTIVE.value, ProgramStatus.RETIRED.value], **course_filters
        )
        assert len(result) == 2
        assert result[0] == self.program
        assert result[1] == self.program2

    def test_get_filtered_programs_retired_false_empty_false(self):
        self.program2 = ProgramFactory(
            title="TestProgram2Retired",
            course_runs=self.course_runs,
            authoring_organizations=self.orgs,
            site=self.site,
            status=ProgramStatus.RETIRED.value,
        )
        self.program3 = ProgramFactory(
            title="TestProgram3Empty", course_runs=None, authoring_organizations=self.orgs, site=self.site
        )
        # exclude retired and empty programs
        course_filters = {"course_runs__in": self.course_runs}
        result = get_filtered_programs(self.site, [ProgramStatus.ACTIVE.value], **course_filters)
        assert len(result) == 1
        assert result[0] == self.program
