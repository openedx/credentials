import uuid
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from openedx_events.learning.data import CourseData, CoursePassingStatusData, UserData, UserPersonalData

from credentials.apps.badges.exceptions import BadgesProcessingError
from credentials.apps.badges.models import (
    BadgePenalty,
    BadgeProgress,
    BadgeRequirement,
    BadgeTemplate,
    CredlyBadgeTemplate,
    CredlyOrganization,
    DataRule,
    Fulfillment,
    PenaltyDataRule,
)
from credentials.apps.badges.processing.generic import identify_user, process_event
from credentials.apps.badges.processing.progression import discover_requirements, process_requirements
from credentials.apps.badges.processing.regression import discover_penalties, process_penalties
from credentials.apps.badges.signals import BADGE_PROGRESS_COMPLETE
from credentials.apps.badges.signals.handlers import handle_badge_completion


COURSE_PASSING_EVENT = "org.openedx.learning.course.passing.status.updated.v1"
COURSE_PASSING_DATA = CoursePassingStatusData(
    is_passing=True,
    course=CourseData(course_key=CourseKey.from_string("course-v1:edX+DemoX.1+2014"), display_name="A"),
    user=UserData(
        id=1,
        is_active=True,
        pii=UserPersonalData(username="test_username", email="test_email", name="John Doe"),
    ),
)
User = get_user_model()


class BadgeRequirementDiscoveryTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site, is_active=True
        )

        self.CCX_COURSE_PASSING_EVENT = "org.openedx.learning.ccx.course.passing.status.updated.v1"

    def test_discovery_eventtype_related_requirements(self):
        BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
        )
        BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=self.CCX_COURSE_PASSING_EVENT,
            description="Test ccx course passing award description",
        )
        BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=self.CCX_COURSE_PASSING_EVENT,
            description="Test ccx course passing revoke description",
        )
        course_passing_requirements = discover_requirements(event_type=COURSE_PASSING_EVENT)
        ccx_course_passing_requirements = discover_requirements(event_type=self.CCX_COURSE_PASSING_EVENT)
        self.assertEqual(course_passing_requirements.count(), 1)
        self.assertEqual(ccx_course_passing_requirements.count(), 2)
        self.assertEqual(course_passing_requirements[0].description, "Test course passing award description")
        self.assertEqual(ccx_course_passing_requirements[0].description, "Test ccx course passing award description")
        self.assertEqual(ccx_course_passing_requirements[1].description, "Test ccx course passing revoke description")


class BadgePenaltyDiscoveryTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site, is_active=True
        )

        self.CCX_COURSE_PASSING_EVENT = "org.openedx.learning.ccx.course.passing.status.updated.v1"

    def test_discovery_eventtype_related_penalties(self):
        penalty1 = BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT)
        penalty1.requirements.add(
            BadgeRequirement.objects.create(
                template=self.badge_template,
                event_type=COURSE_PASSING_EVENT,
                description="Test course passing award description",
            )
        )
        penalty2 = BadgePenalty.objects.create(template=self.badge_template, event_type=self.CCX_COURSE_PASSING_EVENT)
        penalty2.requirements.add(
            BadgeRequirement.objects.create(
                template=self.badge_template,
                event_type=self.CCX_COURSE_PASSING_EVENT,
                description="Test ccx course passing award description",
            )
        )
        penalty3 = BadgePenalty.objects.create(template=self.badge_template, event_type=self.CCX_COURSE_PASSING_EVENT)
        penalty3.requirements.add(
            BadgeRequirement.objects.create(
                template=self.badge_template,
                event_type=self.CCX_COURSE_PASSING_EVENT,
                description="Test ccx course passing revoke description",
            )
        )
        course_passing_penalties = discover_penalties(event_type=COURSE_PASSING_EVENT)
        ccx_course_passing_penalties = discover_penalties(event_type=self.CCX_COURSE_PASSING_EVENT)
        self.assertEqual(course_passing_penalties.count(), 1)
        self.assertEqual(ccx_course_passing_penalties.count(), 2)
        self.assertEqual(
            course_passing_penalties[0].requirements.first().description, "Test course passing award description"
        )
        self.assertEqual(
            ccx_course_passing_penalties[0].requirements.first().description,
            "Test ccx course passing award description",
        )
        self.assertEqual(
            ccx_course_passing_penalties[1].requirements.first().description,
            "Test ccx course passing revoke description",
        )


class TestProcessPenalties(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_username", email="test@example.com", full_name="Test User", lms_user_id=1
        )
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
            is_active=True,
            organization=self.organization,
        )

        self.CCX_COURSE_PASSING_EVENT = "org.openedx.learning.ccx.course.passing.status.updated.v1"

    def test_process_penalties_all_datarules_success(self):
        requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 1",
        )
        requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 2",
        )
        DataRule.objects.create(
            requirement=requirement1,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement2,
            data_path="course.display_name",
            operator="ne",
            value="B",
        )

        progress = BadgeProgress.objects.create(username="test_username", template=self.badge_template)
        Fulfillment.objects.create(progress=progress, requirement=requirement1)
        Fulfillment.objects.create(progress=progress, requirement=requirement2)

        self.assertEqual(BadgeProgress.objects.filter(username="test_username").count(), 1)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 2)
        self.assertEqual(Fulfillment.objects.filter(progress=progress, requirement=requirement1).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(progress=progress, requirement=requirement1).count(), 1)

        bp = BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT)
        bp.requirements.set(
            (requirement1, requirement2),
        )
        PenaltyDataRule.objects.create(
            penalty=bp,
            data_path="course.display_name",
            operator="ne",
            value="test_username1",
        )
        self.badge_template.is_active = True
        self.badge_template.save()
        process_penalties(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 0)

    def test_process_penalties_one_datarule_fail(self):
        requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 1",
        )
        requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 2",
        )
        DataRule.objects.create(
            requirement=requirement1,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement2,
            data_path="course.display_name",
            operator="eq",
            value="B",
        )

        progress = BadgeProgress.objects.create(username="test_username")
        Fulfillment.objects.create(progress=progress, requirement=requirement1)
        Fulfillment.objects.create(progress=progress, requirement=requirement2)

        self.assertEqual(BadgeProgress.objects.filter(username="test_username").count(), 1)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 2)
        self.assertEqual(Fulfillment.objects.filter(progress=progress, requirement=requirement1).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(progress=progress, requirement=requirement1).count(), 1)

        BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT).requirements.set(
            (requirement1, requirement2),
        )
        PenaltyDataRule.objects.create(
            penalty=BadgePenalty.objects.first(),
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        PenaltyDataRule.objects.create(
            penalty=BadgePenalty.objects.first(),
            data_path="course.display_name",
            operator="ne",
            value="A",
        )
        process_penalties(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 2)

    def test_process_single_requirement_penalty(self):
        requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
        )
        DataRule.objects.create(
            requirement=requirement,
            data_path="course.display_name",
            operator="ne",
            value="B",
        )
        progress = BadgeProgress.objects.create(username="test_username", template=self.badge_template)
        Fulfillment.objects.create(progress=progress, requirement=requirement)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 1)

        penalty = BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT)
        penalty.requirements.add(requirement)
        PenaltyDataRule.objects.create(
            penalty=penalty,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        process_penalties(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 0)

    def test_process_one_of_grouped_requirements_penalty(self):
        requirement_a = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
            blend="a_or_b",
        )
        requirement_b = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
            blend="a_or_b",
        )
        DataRule.objects.create(
            requirement=requirement_a,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement_b,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        progress = BadgeProgress.objects.create(username="test_username", template=self.badge_template)
        Fulfillment.objects.create(progress=progress, requirement=requirement_a)
        Fulfillment.objects.create(progress=progress, requirement=requirement_b)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 2)

        penalty = BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT)
        penalty.requirements.add(requirement_b)
        PenaltyDataRule.objects.create(
            penalty=penalty,
            data_path="course.display_name",
            operator="ne",
            value="B",
        )
        process_penalties(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 1)

    def test_process_mixed_penalty(self):
        requirement_a = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
            blend="a_or_b",
        )
        requirement_b = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
            blend="a_or_b",
        )
        requirement_c = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description",
        )
        DataRule.objects.create(
            requirement=requirement_a,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement_b,
            data_path="course.display_name",
            operator="eq",
            value="B",
        )
        DataRule.objects.create(
            requirement=requirement_c,
            data_path="course.display_name",
            operator="ne",
            value="C",
        )
        progress = BadgeProgress.objects.create(username="test_username", template=self.badge_template)
        Fulfillment.objects.create(progress=progress, requirement=requirement_a)
        Fulfillment.objects.create(progress=progress, requirement=requirement_c)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 2)

        penalty = BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT)
        penalty.requirements.add(requirement_a, requirement_c)
        PenaltyDataRule.objects.create(
            penalty=penalty,
            data_path="course.display_name",
            operator="ne",
            value="B",
        )
        process_penalties(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(progress=progress).count(), 0)


class TestProcessRequirements(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
            organization=self.organization,
            is_active=True,
        )

        self.CCX_COURSE_PASSING_EVENT = "org.openedx.learning.ccx.course.passing.status.updated.v1"
        self.user = identify_user(event_type=COURSE_PASSING_EVENT, event_payload=COURSE_PASSING_DATA)

        # disconnect BADGE_PROGRESS_COMPLETE signal
        BADGE_PROGRESS_COMPLETE.disconnect(handle_badge_completion)

    # test cases
    #     A course completion - course A w/o a group;
    #     A or B course completion - courses A, B have the same group value;
    #     A or B or C course completion - courses A, B, C have the same group value;
    #     A or - courses A is the only course in the group;
    #     (A or B) and C - A, B have the same group value; course C w/o a group;
    #     (A or B) and (C or D) - courses A, B have the same group value; courses C, D have the same group value;

    def test_course_a_completion(self):
        requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A course passing award description",
        )
        DataRule.objects.create(
            requirement=requirement,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement).count(), 1)
        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def test_course_a_or_b_completion(self):
        requirement_a = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B course passing award description",
            blend="a_or_b",
        )
        requirement_b = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B course passing award description",
            blend="a_or_b",
        )
        DataRule.objects.create(
            requirement=requirement_a,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement_b,
            data_path="course.display_name",
            operator="eq",
            value="B",
        )
        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_a).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_b).count(), 0)
        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def test_course_a_or_b_or_c_completion(self):
        requirement_a = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B or C course passing award description",
            blend="a_or_b_or_c",
        )
        requirement_b = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B or C course passing award description",
            blend="a_or_b_or_c",
        )
        requirement_c = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B or C course passing award description",
            blend="a_or_b_or_c",
        )
        DataRule.objects.create(
            requirement=requirement_a,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement_b,
            data_path="course.display_name",
            operator="eq",
            value="B",
        )
        DataRule.objects.create(
            requirement=requirement_c,
            data_path="course.display_name",
            operator="eq",
            value="C",
        )
        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_a).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_b).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_c).count(), 0)
        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def test_course_a_or_completion(self):
        requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or course passing award description",
            blend="a_or",
        )
        DataRule.objects.create(
            requirement=requirement,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement).count(), 1)
        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def test_course_a_or_b_and_c_completion(self):
        requirement_a = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B course passing award description",
            blend="a_or_b",
        )
        requirement_b = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B course passing award description",
            blend="a_or_b",
        )
        requirement_c = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="C course passing award description",
        )
        DataRule.objects.create(
            requirement=requirement_a,
            data_path="course.display_name",
            operator="ne",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement_c,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )

        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_a).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_b).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_c).count(), 1)
        self.assertFalse(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

        DataRule.objects.create(
            requirement=requirement_b,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )

        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)

        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_a).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_b).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_c).count(), 1)

        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def test_course_a_or_b_and_c_or_d_completion(self):
        requirement_a = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B course passing award description",
            blend="a_or_b",
        )
        requirement_b = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="A or B course passing award description",
            blend="a_or_b",
        )
        requirement_c = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="C or D course passing award description",
            blend="c_or_d",
        )
        requirement_d = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type=COURSE_PASSING_EVENT,
            description="C or D course passing award description",
            blend="c_or_d",
        )
        DataRule.objects.create(
            requirement=requirement_a,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        DataRule.objects.create(
            requirement=requirement_b,
            data_path="course.display_name",
            operator="eq",
            value="B",
        )
        DataRule.objects.create(
            requirement=requirement_d,
            data_path="course.display_name",
            operator="eq",
            value="D",
        )

        self.assertFalse(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)

        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_a).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_b).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_c).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_d).count(), 0)
        self.assertFalse(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

        DataRule.objects.create(
            requirement=requirement_c,
            data_path="course.display_name",
            operator="eq",
            value="A",
        )
        process_requirements(COURSE_PASSING_EVENT, "test_username", COURSE_PASSING_DATA)

        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_a).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_b).count(), 0)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_c).count(), 1)
        self.assertEqual(Fulfillment.objects.filter(requirement=requirement_d).count(), 0)
        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def tearDown(self):
        BADGE_PROGRESS_COMPLETE.connect(handle_badge_completion)


class TestIdentifyUser(TestCase):
    def test_identify_user(self):
        username = identify_user(event_type=COURSE_PASSING_EVENT, event_payload=COURSE_PASSING_DATA)
        self.assertEqual(username, "test_username")

    def test_identify_user_not_found(self):
        event_type = "unknown_event_type"
        event_payload = None

        with self.assertRaises(BadgesProcessingError) as cm:
            identify_user(event_type="unknown_event_type", event_payload=event_payload)

        self.assertEqual(
            str(cm.exception),
            f"User data cannot be found (got: None): {event_payload}. "
            f"Does event {event_type} include user data at all?",
        )


def mock_progress_regress(*args, **kwargs):
    return None


class TestProcessEvent(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test_api_key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
            organization=self.organization,
            is_active=True,
        )
        DataRule.objects.create(
            requirement=BadgeRequirement.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT),
            data_path="is_passing",
            operator="eq",
            value="True",
        )
        PenaltyDataRule.objects.create(
            penalty=BadgePenalty.objects.create(template=self.badge_template, event_type=COURSE_PASSING_EVENT),
            data_path="is_passing",
            operator="eq",
            value="False",
        )
        self.sender = MagicMock()
        self.sender.event_type = COURSE_PASSING_EVENT

    @patch.object(BadgeProgress, "progress", mock_progress_regress)
    def test_process_event_passing(self):
        event_payload = COURSE_PASSING_DATA
        process_event(sender=self.sender, kwargs=event_payload)
        self.assertTrue(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    def test_process_event_not_passing(self):
        event_payload = CoursePassingStatusData(
            is_passing=False,
            course=CourseData(course_key=CourseKey.from_string("course-v1:edX+DemoX.1+2014"), display_name="A"),
            user=UserData(
                id=1,
                is_active=True,
                pii=UserPersonalData(username="test_username", email="test_email", name="John Doe"),
            ),
        )
        process_event(sender=self.sender, kwargs=event_payload)
        self.assertFalse(BadgeProgress.for_user(username="test_username", template_id=self.badge_template.id).completed)

    @patch.object(BadgeProgress, "regress", mock_progress_regress)
    def test_process_event_not_found(self):
        sender = MagicMock()
        sender.event_type = "unknown_event_type"
        event_payload = None

        with patch("credentials.apps.badges.processing.generic.logger.error") as mock_event_not_found:
            process_event(sender=sender, kwargs=event_payload)
            mock_event_not_found.assert_called_once()

    def test_process_event_no_user_data(self):
        event_payload = CoursePassingStatusData(
            is_passing=True,
            course=CourseData(course_key=CourseKey.from_string("course-v1:edX+DemoX.1+2014"), display_name="A"),
            user=None,
        )

        with patch("credentials.apps.badges.processing.generic.logger.error") as mock_no_user_data:
            process_event(sender=self.sender, kwargs=event_payload)
            mock_no_user_data.assert_called_once()
