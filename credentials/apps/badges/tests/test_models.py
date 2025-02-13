import uuid
from unittest.mock import patch

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.test import TestCase
from faker import Faker
from openedx_events.learning.data import BadgeData, BadgeTemplateData, UserData, UserPersonalData

from credentials.apps.badges.models import (
    AccredibleAPIConfig,
    AccredibleBadge,
    AccredibleGroup,
    BadgePenalty,
    BadgeProgress,
    BadgeRequirement,
    BadgeTemplate,
    CredlyBadge,
    CredlyBadgeTemplate,
    CredlyOrganization,
    DataRule,
    Fulfillment,
    PenaltyDataRule,
)
from credentials.apps.core.models import User


class DataRulesTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
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
            template=self.badge_template1,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
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
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
        )

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
            template=self.credlybadge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
        )
        self.requirement4 = BadgeRequirement.objects.create(
            template=self.credlybadge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
        )

        self.requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )

    def test_multiple_requirements_for_badgetemplate(self):
        requirements = BadgeRequirement.objects.filter(template=self.badge_template)

        self.assertEqual(requirements.count(), 3)
        self.assertIn(self.requirement1, requirements)
        self.assertIn(self.requirement2, requirements)

    def test_multiple_requirements_for_credlybadgetemplate(self):
        requirements = BadgeRequirement.objects.filter(template=self.credlybadge_template)

        self.assertEqual(requirements.count(), 2)
        self.assertIn(self.requirement3, requirements)
        self.assertIn(self.requirement4, requirements)

    def test_fulfill(self):
        username = "test_user"
        template_id = self.badge_template.id
        progress = BadgeProgress.objects.create(username=username, template=self.badge_template)
        with patch("credentials.apps.badges.models.notify_requirement_fulfilled") as mock_notify:
            created = self.requirement.fulfill(username)
            fulfillment = Fulfillment.objects.get(
                progress=progress,
                requirement=self.requirement,
                blend=self.requirement.blend,
            )

            self.assertTrue(created)
            self.assertTrue(mock_notify.called)
            mock_notify.assert_called_with(
                sender=self.requirement,
                username=username,
                badge_template_id=template_id,
                fulfillment_id=fulfillment.id,
            )

    def test_is_active(self):
        self.requirement.template.is_active = True
        self.assertTrue(self.requirement.is_active)

        self.requirement.template.is_active = False
        self.assertFalse(self.requirement.is_active)


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
            template=self.badge_template1,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
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
            blend="group1",
        )
        self.badge_requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            blend="group1",
        )
        self.badge_requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
        )

    def test_requirement_group(self):
        groups = self.badge_template.requirements.filter(blend="group1")
        self.assertEqual(groups.count(), 2)
        self.assertIsNone(self.badge_requirement3.blend)


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
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="A",
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="B",
        )
        self.requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            description="Test description",
            blend="C",
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
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
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
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="A",
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="B",
        )

        self.group_requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="test-group1",
        )
        self.group_requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="test-group1",
        )

        self.group_requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="test-group2",
        )
        self.group_requirement4 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
            blend="test-group2",
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
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            lms_user_id=1,
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


class BadgePenaltyTestCase(TestCase):
    def setUp(self):
        self.fake = Faker()
        self.badge_template = BadgeTemplate.objects.create(
            uuid=self.fake.uuid4(),
            name="test_template",
            state="draft",
            site=Site.objects.create(domain="test_domain", name="test_name"),
            is_active=True,
        )
        self.badge_requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )
        self.badge_penalty = BadgePenalty.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.student.registration.completed.v1",
        )
        self.badge_penalty.requirements.add(self.badge_requirement)

    def test_apply_rules_with_empty_rules(self):
        data = {"key": "value"}
        self.assertFalse(self.badge_penalty.apply_rules(data))

    def test_apply_rules_with_non_empty_rules(self):
        data = {"key": "value"}
        self.badge_penalty.rules.create(data_path="key", operator="eq", value="value")
        self.assertTrue(self.badge_penalty.apply_rules(data))

    def test_reset_requirements(self):
        username = "test-username"
        with patch("credentials.apps.badges.models.BadgeRequirement.reset") as mock_reset:
            self.badge_penalty.reset_requirements(username)
            mock_reset.assert_called_once_with(username)

    def test_is_active(self):
        self.assertTrue(self.badge_penalty.is_active)


class IsGroupFulfilledTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.badge_requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            blend="group1",
        )
        self.badge_requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.ccx.course.passing.status.updated.v1",
            blend="group1",
        )
        self.badge_requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
        )
        self.username = "test_user"

    def test_is_group_fulfilled_with_fulfilled_requirements(self):
        progress = BadgeProgress.objects.create(username=self.username, template=self.badge_template)
        Fulfillment.objects.create(progress=progress, requirement=self.badge_requirement1)

        is_fulfilled = BadgeRequirement.is_group_fulfilled(
            group="group1", template=self.badge_template, username=self.username
        )

        self.assertTrue(is_fulfilled)

    def test_is_group_fulfilled_with_unfulfilled_requirements(self):
        is_fulfilled = BadgeRequirement.is_group_fulfilled(
            group="group1", template=self.badge_template, username=self.username
        )

        self.assertFalse(is_fulfilled)

    def test_is_group_fulfilled_with_invalid_group(self):
        is_fulfilled = BadgeRequirement.is_group_fulfilled(
            group="invalid_group", template=self.badge_template, username=self.username
        )

        self.assertFalse(is_fulfilled)


class CredlyOrganizationTestCase(TestCase):
    def setUp(self):
        self.fake = Faker()
        self.uuid = self.fake.uuid4()
        self.organization = CredlyOrganization.objects.create(
            uuid=self.uuid, api_key="test-api-key", name="test_organization"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.organization), "test_organization")

    def test_get_all_organization_ids(self):
        organization_ids = [str(uuid) for uuid in CredlyOrganization.get_all_organization_ids()]
        self.assertEqual(organization_ids, [self.uuid])

    def test_get_preconfigured_organizations(self):
        preconfigured_organizations = CredlyOrganization.get_preconfigured_organizations()
        self.assertEqual(
            preconfigured_organizations,
            settings.BADGES_CONFIG["credly"].get("ORGANIZATIONS", {}),
        )

    def test_is_preconfigured(self):
        with patch(
            "credentials.apps.badges.models.CredlyOrganization.get_preconfigured_organizations"
        ) as mock_get_preconfigured:
            mock_get_preconfigured.return_value = {str(self.uuid): "Test Organization"}
            self.assertTrue(self.organization.is_preconfigured)
            mock_get_preconfigured.assert_called_once()


class BadgeProgressTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.badge_progress = BadgeProgress.objects.create(template=self.badge_template, username="test_user")

    def test_reset_progress(self):
        Fulfillment.objects.create(progress=self.badge_progress)
        self.assertEqual(Fulfillment.objects.filter(progress=self.badge_progress).count(), 1)

        self.badge_progress.reset()

        self.assertEqual(Fulfillment.objects.filter(progress=self.badge_progress).count(), 0)


class BadgePenaltyIsActiveTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
        )
        self.requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )
        self.penalty = BadgePenalty.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
        )

    def test_is_active(self):
        self.penalty.template.is_active = True
        self.assertTrue(self.penalty.is_active)

    def test_is_not_active(self):
        self.penalty.template.is_active = False
        self.assertFalse(self.penalty.is_active)


class DataRuleIsActiveTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )
        self.rule = DataRule.objects.create(
            requirement=self.requirement,
            data_path="course_passing_status.user.pii.username",
            operator="eq",
            value="cucumber1997",
        )

    def test_is_active(self):
        self.rule.requirement.template.is_active = True
        self.assertTrue(self.rule.is_active)

        self.rule.requirement.template.is_active = False
        self.assertFalse(self.rule.is_active)


class BadgeTemplateTestCase(TestCase):
    def test_by_uuid(self):
        template_uuid = uuid.uuid4()
        site = Site.objects.create(domain="test_domain", name="test_name")
        badge_template = BadgeTemplate.objects.create(uuid=template_uuid, origin=BadgeTemplate.ORIGIN, site=site)

        retrieved_template = BadgeTemplate.by_uuid(template_uuid)

        self.assertEqual(retrieved_template, badge_template)


class CredlyBadgeTemplateTestCase(TestCase):
    def setUp(self):
        uuid4 = uuid.uuid4()
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid4, api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization,
            uuid=uuid4,
            name="test_template",
            state="draft",
            site=self.site,
        )

    def test_management_url(self):
        credly_host_base_url = "https://example.com/"
        with patch("credentials.apps.badges.models.get_credly_base_url") as mock_get_credly_base_url:
            mock_get_credly_base_url.return_value = credly_host_base_url
            expected_url = (
                f"{credly_host_base_url}mgmt/organizations/"
                f"{self.organization.uuid}/badges/templates/{self.badge_template.uuid}/details"
            )
            self.assertEqual(self.badge_template.management_url, expected_url)
            mock_get_credly_base_url.assert_called_with(settings)


class PenaltyDataruleIsActiveTestCase(TestCase):
    def setUp(self):
        self.organization = CredlyOrganization.objects.create(
            uuid=uuid.uuid4(), api_key="test-api-key", name="test_organization"
        )
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.credlybadge_template = CredlyBadgeTemplate.objects.create(
            organization=self.organization,
            uuid=uuid.uuid4(),
            name="test_template",
            state="draft",
            site=self.site,
        )

        self.requirement = BadgeRequirement.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
            description="Test description",
        )
        self.penalty = BadgePenalty.objects.create(
            template=self.badge_template,
            event_type="org.openedx.learning.course.passing.status.updated.v1",
        )
        self.rule = PenaltyDataRule.objects.create(
            penalty=self.penalty,
            data_path="course_passing_status.user.pii.username",
            operator="eq",
            value="cucumber1997",
        )

    def test_is_active(self):
        self.requirement.template.is_active = True
        self.assertTrue(self.rule.is_active)

        self.requirement.template.is_active = False
        self.assertFalse(self.rule.is_active)


class AccredibleGroupTestCase(TestCase):
    def setUp(self):
        self.api_config = AccredibleAPIConfig.objects.create(api_key="test-api-key", name="test_config")
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.group = AccredibleGroup.objects.create(
            api_config=self.api_config,
            id=55,
            name="test_group",
            site=self.site,
        )

    def test_management_url(self):
        credly_host_base_url = "https://example.com/"
        with patch("credentials.apps.badges.models.get_accredible_base_url") as mock_get_accredible_base_url:
            mock_get_accredible_base_url.return_value = credly_host_base_url
            expected_url = f"{credly_host_base_url}issuer/dashboard/group/{self.group.id}/information-and-appearance"
            self.assertEqual(self.group.management_url, expected_url)
            mock_get_accredible_base_url.assert_called_with(settings)


class AccredibleAPIConfigTestCase(TestCase):
    def setUp(self):
        self.api_config = AccredibleAPIConfig.objects.create(
            api_key="test-api-key",
            name="test_config",
        )

    def test_get_all_api_config_ids(self):
        organization_ids = list(AccredibleAPIConfig.get_all_api_config_ids())
        self.assertEqual(organization_ids, [self.api_config.id])


class AccredibleBadgeAsBadgeDataTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            lms_user_id=1,
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
        self.badge = AccredibleBadge.objects.create(
            username="test_user",
            credential_content_type=ContentType.objects.get_for_model(self.credential),
            credential_id=self.credential.id,
            state=AccredibleBadge.STATES.created,
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
