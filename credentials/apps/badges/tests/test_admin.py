import uuid

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase, override_settings

from credentials.apps.badges.admin import CredlyOrganizationAdmin
from credentials.apps.badges.models import CredlyOrganization

PRECONFIGURED_UUID = str(uuid.uuid4())


@override_settings(BADGES_CONFIG={"credly": {"ORGANIZATIONS": {PRECONFIGURED_UUID: "preconfigured-api-key"}}})
class CredlyOrganizationAdminTestCase(TestCase):
    def setUp(self):
        self.admin = CredlyOrganizationAdmin(CredlyOrganization, AdminSite())
        self.request = RequestFactory().get("/")
        self.preconfigured = CredlyOrganization.objects.create(uuid=PRECONFIGURED_UUID, name="preconfigured")
        self.regular = CredlyOrganization.objects.create(uuid=uuid.uuid4(), name="regular", api_key="key")

    def _fieldset_fields(self, obj):
        fields = []
        for _, options in self.admin.get_fieldsets(self.request, obj):
            fields.extend(options["fields"])
        return fields

    def test_add_form_exposes_editable_credentials(self):
        fields = self._fieldset_fields(obj=None)

        self.assertIn("api_key", fields)
        self.assertIn("oauth_client_id", fields)
        self.assertIn("oauth_client_secret", fields)
        self.assertNotIn("api_key_hidden", fields)
        self.assertEqual(self.admin.get_readonly_fields(self.request), ["name"])

    def test_regular_organization_exposes_editable_credentials(self):
        fields = self._fieldset_fields(self.regular)

        self.assertIn("api_key", fields)
        self.assertNotIn("api_key_hidden", fields)
        self.assertEqual(self.admin.get_readonly_fields(self.request, self.regular), ["name"])

    def test_preconfigured_organization_hides_api_key(self):
        fields = self._fieldset_fields(self.preconfigured)

        self.assertIn("api_key_hidden", fields)
        self.assertNotIn("api_key", fields)

    def test_preconfigured_organization_credentials_are_readonly(self):
        readonly_fields = self.admin.get_readonly_fields(self.request, self.preconfigured)

        self.assertCountEqual(readonly_fields, ["name", "api_key_hidden", "oauth_client_id", "oauth_client_secret"])

    def test_api_key_hidden_display(self):
        self.assertEqual(self.admin.api_key_hidden(self.preconfigured), "Pre-configured from the environment.")
        self.assertEqual(self.admin.api_key_hidden(self.regular), "key")
