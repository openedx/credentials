import uuid
from unittest.mock import MagicMock, patch

from django import forms
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from credentials.apps.badges.admin_forms import (
    BadgePenaltyForm,
    CredlyOrganizationAdminForm,
    DataRuleExtensionsMixin,
    ParentMixin,
)
from credentials.apps.badges.exceptions import BadgeProviderError
from credentials.apps.badges.models import BadgeRequirement, BadgeTemplate

COURSE_PASSING_EVENT = "org.openedx.learning.course.passing.status.updated.v1"


class BadgePenaltyFormTestCase(TestCase):
    def setUp(self):
        self.site = Site.objects.create(domain="test_domain", name="test_name")
        self.badge_template1 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.badge_template2 = BadgeTemplate.objects.create(
            uuid=uuid.uuid4(), name="test_template", state="draft", site=self.site
        )
        self.requirement1 = BadgeRequirement.objects.create(
            template=self.badge_template1,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 1",
        )
        self.requirement2 = BadgeRequirement.objects.create(
            template=self.badge_template2,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 2",
        )
        self.requirement3 = BadgeRequirement.objects.create(
            template=self.badge_template2,
            event_type=COURSE_PASSING_EVENT,
            description="Test course passing award description 3",
        )

    def test_clean_requirements_same_template(self):
        form = BadgePenaltyForm()
        form.cleaned_data = {
            "template": self.badge_template2,
            "requirements": [
                self.requirement2,
                self.requirement3,
            ],
        }
        self.assertEqual(
            form.clean(),
            {
                "template": self.badge_template2,
                "requirements": [
                    self.requirement2,
                    self.requirement3,
                ],
            },
        )

    def test_clean_requirements_different_template(self):
        form = BadgePenaltyForm()
        form.cleaned_data = {
            "template": self.badge_template1,
            "requirements": [
                self.requirement2,
                self.requirement1,
            ],
        }

        with self.assertRaises(forms.ValidationError) as cm:
            form.clean()

        self.assertEqual(str(cm.exception), "['All requirements must belong to the same template.']")

    @override_settings(BADGES_CONFIG={"credly": {"ORGANIZATIONS": {}}})
    def test_clean(self):
        form = CredlyOrganizationAdminForm()
        form.cleaned_data = {
            "uuid": "test_uuid",
            "api_key": "test_api_key",
        }

        with patch(
            "credentials.apps.badges.models.CredlyOrganization.get_preconfigured_organizations"
        ) as mock_get_orgs:
            mock_get_orgs.return_value = {}

            with patch("credentials.apps.badges.admin_forms.CredlyAPIClient") as mock_client:
                mock_client.return_value = MagicMock()

                form.clean()

                mock_get_orgs.assert_called_once()
                mock_client.assert_called_once_with("test_uuid", "test_api_key")

    @override_settings(BADGES_CONFIG={"credly": {"ORGANIZATIONS": {"test_uuid": "test_api_key"}}})
    def test_clean_with_configured_organization(self):
        form = CredlyOrganizationAdminForm()
        form.cleaned_data = {
            "uuid": "test_uuid",
            "api_key": None,
        }

        with patch(
            "credentials.apps.badges.models.CredlyOrganization.get_preconfigured_organizations"
        ) as mock_get_orgs:
            mock_get_orgs.return_value = {"test_uuid": "test_org"}

            with patch("credentials.apps.badges.admin_forms.CredlyAPIClient") as mock_client:
                mock_client.return_value = MagicMock()

                form.clean()

                mock_get_orgs.assert_called_once()
                mock_client.assert_called_once_with("test_uuid", "test_api_key")

    def test_clean_with_invalid_organization(self):
        form = CredlyOrganizationAdminForm()
        form.cleaned_data = {
            "uuid": "invalid_uuid",
            "api_key": "test_api_key",
        }

        with patch(
            "credentials.apps.badges.models.CredlyOrganization.get_preconfigured_organizations"
        ) as mock_get_orgs:
            mock_get_orgs.return_value = {"test_uuid": "test_org"}

            with self.assertRaises(BadgeProviderError) as cm:
                form.clean()

            self.assertIn("You specified an invalid authorization token.", str(cm.exception))

    def test_clean_cannot_provide_api_key_for_configured_organization(self):
        form = CredlyOrganizationAdminForm()
        form.cleaned_data = {
            "uuid": "test_uuid",
            "api_key": "test_api_key",
        }

        with patch(
            "credentials.apps.badges.models.CredlyOrganization.get_preconfigured_organizations"
        ) as mock_get_orgs:
            mock_get_orgs.return_value = {"test_uuid": "test_org"}

            with self.assertRaises(forms.ValidationError) as cm:
                form.clean()

            self.assertEqual(
                str(cm.exception),
                '["You can\'t provide an API key for a configured organization."]',
            )

    def test_ensure_organization_exists(self):
        form = CredlyOrganizationAdminForm()
        api_client = MagicMock()
        api_client.fetch_organization.return_value = {"data": {"org_id": "test_org_id"}}

        form.ensure_organization_exists(api_client)

        api_client.fetch_organization.assert_called_once()
        self.assertEqual(form.api_data, {"org_id": "test_org_id"})

    def test_ensure_organization_exists_with_error(self):
        form = CredlyOrganizationAdminForm()
        api_client = MagicMock()
        api_client.fetch_organization.side_effect = BadgeProviderError("API Error")

        with self.assertRaises(BadgeProviderError) as cm:
            form.ensure_organization_exists(api_client)

        api_client.fetch_organization.assert_called_once()
        self.assertEqual(str(cm.exception), "API Error")


class TestParentMixin(ParentMixin):
    pass


class ParentMixinTestCase(TestCase):
    def setUp(self):
        self.instance = MagicMock()
        self.instance.some_attribute = "some_value"

        self.mixin = TestParentMixin()
        self.mixin.instance = self.instance

    def test_get_form_kwargs_passes_parent_instance(self):
        with patch.object(
            TestParentMixin,
            "get_form_kwargs",
            return_value={"parent_instance": self.instance},
        ) as super_method:
            result = self.mixin.get_form_kwargs(0)

            super_method.assert_called_once_with(0)

            self.assertIn("parent_instance", result)
            self.assertEqual(result["parent_instance"], self.instance)


class TestForm(DataRuleExtensionsMixin, forms.Form):
    data_path = forms.ChoiceField(choices=[])
    value = forms.CharField()


class DataRuleExtensionsMixinTestCase(TestCase):
    def setUp(self):
        self.parent_instance = MagicMock()
        self.parent_instance.event_type = COURSE_PASSING_EVENT

    def test_init_sets_choices_based_on_event_type(self):
        form = TestForm(parent_instance=self.parent_instance)
        self.assertEqual(
            form.fields["data_path"].choices,
            [("is_passing", "is_passing"), ("course.course_key", "course.course_key")],
        )

    def test_clean_with_valid_boolean_value(self):
        form = TestForm(
            data={"data_path": "is_passing", "value": "True"},
            parent_instance=self.parent_instance,
        )
        form.is_valid()
        self.assertRaises(KeyError, lambda: form.errors["__all__"])

    def test_clean_with_invalid_boolean_value(self):
        form = TestForm(
            data={"data_path": "is_passing", "value": "invalid"},
            parent_instance=self.parent_instance,
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["__all__"], ["Value must be a boolean."])

    def test_clean_with_non_boolean_data_path(self):
        form = TestForm(
            data={"data_path": "course.course_key", "value": "some_value"},
            parent_instance=self.parent_instance,
        )
        form.is_valid()
        self.assertRaises(KeyError, lambda: form.errors["__all__"])
