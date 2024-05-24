import uuid

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.test import TestCase
from openedx_events.learning.data import BadgeData, UserData, UserPersonalData, BadgeTemplateData

from credentials.apps.badges.models import (
    BadgeProgress,
    BadgeRequirement,
    BadgeTemplate,
    CredlyBadge,
    CredlyBadgeTemplate,
    CredlyOrganization,
    DataRule,
    Fulfillment,
)
from credentials.apps.core.models import User


class DataRulesTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization, uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )

    def test_multiple_data_rules_for_requirement(self):
        data_rule1 = DataRule.objects.create(
            requirement=self.requirement,
            data_path="course_passing_status.user.pii.username",
            operator="eq",
            value="cucumber1997",
        )
        data_rule2 = DataRule.objects.create(
            requirement=self.requirement,
            data_path="course_passing_status.user.pii.email",
            operator="eq",
            value="test@example.com",
        )

        data_rules = DataRule.objects.filter(requirement=self.requirement)

        self.assertEqual(data_rules.count(), 2)
        self.assertIn(data_rule1, data_rules)
        self.assertIn(data_rule2, data_rules)


class RequirementApplyRulesCheckTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template1 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template1", state="draft", site=self.site
        )
        self.badge_template2 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template2", state="draft", site=self.site
        )
        self.badge_requirement = BadgeRequirement.objects.create(
            template=self.badge_template1, event_type="org.openedx.learning.course.passing.status.updated.v1"
        )
        self.data_rule1 = DataRule.objects.create(
            requirement=self.badge_requirement,
            data_path="course_passing_status.user.pii.username",
            operator="eq",
            value="test-username",
        )
        self.data_rule2 = DataRule.objects.create(
            requirement=self.badge_requirement,
            data_path="course_passing_status.user.pii.email",
            operator="eq",
            value="test@example.com",
        )
        self.data_rule = DataRule.objects.create

    def test_apply_rules_check_success(self):
        data = {"course_passing_status": {"user": {"pii": {"username": "test-username", "email": "test@example.com"}}}}
        self.assertTrue(self.badge_requirement.apply_rules(data))

    def test_apply_rules_check_failed(self):
        data = {"course_passing_status": {"user": {"pii": {"username": "test-username2", "email": "test@example.com"}}}}
        self.assertFalse(self.badge_requirement.apply_rules(data))


class BadgeRequirementTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.credlybadge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization, uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )

    def test_multiple_requirements_for_badgetemplate(self):
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )
        self.requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
        )

        requirements = BadgeRequirement.objects.filter(template=self.badge_template)

        self.assertEqual(requirements.count(), 3)
        self.assertIn(self.requirement1, requirements)
        self.assertIn(self.requirement2, requirements)
        self.assertIn(self.requirement3, requirements)

    def test_multiple_requirements_for_credlybadgetemplate(self):
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.credlybadge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.credlybadge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
        )
        self.requirement3 = BadgeRequirement.objects.create(
            template=self.credlybadge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )

        requirements = BadgeRequirement.objects.filter(template=self.credlybadge_template)

        self.assertEqual(requirements.count(), 3)
        self.assertIn(self.requirement1, requirements)
        self.assertIn(self.requirement2, requirements)
        self.assertIn(self.requirement3, requirements)


class RequirementFulfillmentCheckTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template1 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template1", state="draft", site=self.site
        )
        self.badge_template2 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template2", state="draft", site=self.site
        )
        self.badge_progress = BadgeProgress.objects.create(template=self.badge_template1, username="test1")
        self.badge_requirement = BadgeRequirement.objects.create(
            template=self.badge_template1, event_type="org.openedx.learning.course.passing.status.updated.v1"
        )
        self.fulfillment = Fulfillment.objects.create(progress=self.badge_progress, requirement=self.badge_requirement)

    def test_fulfillment_check_success(self):
        is_fulfilled = self.badge_requirement.is_fulfilled("test1")
        self.assertTrue(is_fulfilled)

    def test_fulfillment_check_wrong_username(self):
        is_fulfilled = self.badge_requirement.is_fulfilled("asd")
        self.assertFalse(is_fulfilled)


class BadgeRequirementGroupTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.badge_requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            group="group1",
        )
        self.badge_requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            group="group1",
        )
        self.badge_requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template, event_type="org.openedx.learning.course.passing.status.updated.v1"
        )

    def test_requirement_group(self):
        group = self.badge_template.requirements.filter(group="group1")
        self.assertEqual(group.count(), 2)
        self.assertIsNone(self.badge_requirement3.group)


class BadgeTemplateUserProgressTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.credlybadge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization, uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="A"
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="B"
        )
        self.requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
            group="C"
        )

    def test_user_progress_success(self):
        Fulfillment.objects.create(
            progress=BadgeProgress.objects.create(username="test_user", template=self.badge_template),
            requirement=self.requirement1,
        )
        self.assertEqual(self.badge_template.user_progress("test_user"), 0.33)

    def test_user_progress_no_fulfillments(self):
        Fulfillment.objects.filter(progress__template=self.badge_template).delete()
        self.assertEqual(self.badge_template.user_progress("test_user"), 0.0)

    def test_user_progress_no_requirements(self):
        BadgeRequirement.objects.filter(template=self.badge_template).delete()
        self.assertEqual(self.badge_template.user_progress("test_user"), 0.0)


class BadgeTemplateUserCompletionTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.credlybadge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization, uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )

    def test_is_completed_success(self):
        Fulfillment.objects.create(
            progress=BadgeProgress.objects.create(username="test_user", template=self.badge_template),
            requirement=self.requirement1,
        )
        self.assertTrue(self.badge_template.is_completed("test_user"))

    def test_is_completed_failure(self):
        self.assertFalse(self.badge_template.is_completed("test_usfer"))

    def test_is_completed_no_requirements(self):
        BadgeRequirement.objects.filter(template=self.badge_template).delete()
        self.assertEqual(self.badge_template.is_completed("test_user"), 0.0)


class BadgeTemplateRatioTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.credlybadge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization, uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="A"
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="B"
        )

        self.group_requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="test-group1",
        )
        self.group_requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="test-group1",
        )

        self.group_requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="test-group2",
        )
        self.group_requirement4 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            group="test-group2",
        )
        self.progress = BadgeProgress.objects.create(username="test_user", template=self.badge_template)

    def test_ratio_no_fulfillments(self):
        self.assertEqual(self.progress.ratio, 0.00)

    def test_ratio_success(self):
        Fulfillment.objects.create(
            progress=self.progress,
            requirement=self.requirement1,
        )
        self.assertEqual(self.progress.ratio, 0.25)

        Fulfillment.objects.create(
            progress=self.progress,
            requirement=self.requirement2,
        )
        self.assertEqual(self.progress.ratio, 0.50)

        Fulfillment.objects.create(
            progress=self.progress,
            requirement=self.group_requirement1,
        )
        self.assertEqual(self.progress.ratio, 0.75)

        Fulfillment.objects.create(
            progress=self.progress,
            requirement=self.group_requirement3,
        )
        self.assertEqual(self.progress.ratio, 1.00)

    def test_ratio_no_requirements(self):
        BadgeRequirement.objects.filter(template=self.badge_template).delete()
        self.assertEqual(self.progress.ratio, 0.00)


class CredlyBadgeAsBadgeDataTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user", email="test@example.com", full_name="Test User", lms_user_id=1
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.credential = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(),
            origin="test_origin",
            name="test_template",
            description="test_description",
            icon="test_icon",
            site=self.site,
        )
        self.badge = CredlyBadge.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.credential),
            credential_id=self.credential.id,
            state=CredlyBadge.STATES.pending,
            uuid=uuid.uuid4(),
        )

    def test_as_badge_data(self):
        expected_badge_data = BadgeData(
            uuid=str(self.badge.uuid),
            user=UserData(
                pii=UserPersonalData(
                    username=self.user.username,
                    email=self.user.email,
                    name=self.user.get_full_name(),
                ),
                id=self.user.lms_user_id,
                is_active=self.user.is_active,
            ),
            template=BadgeTemplateData(
                uuid=str(self.credential.uuid),
                origin=self.credential.origin,
                name=self.credential.name,
                description=self.credential.description,
                image_url=str(self.credential.icon),
            ),
        )
        actual_badge_data = self.badge.as_badge_data()
        self.assertEqual(actual_badge_data, expected_badge_data)
