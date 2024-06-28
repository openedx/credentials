"""
Tests for credentials rendering views.
"""

import uuid
from unittest.mock import PropertyMock, patch

import ddt
import responses
from django.template import Context, Template
from django.template.loader import select_template
from django.test import TestCase
from django.urls import reverse
from django.utils.text import slugify
from faker import Faker
from waffle.testutils import override_switch

from credentials.apps.catalog.data import OrganizationDetails, ProgramDetails
from credentials.apps.catalog.tests.factories import CourseFactory, CourseRunFactory, ProgramFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, SiteConfigurationFactory, UserFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.exceptions import MissingCertificateLogoError
from credentials.apps.credentials.models import ProgramCertificate, UserCredential
from credentials.apps.credentials.templatetags import i18n_assets
from credentials.apps.credentials.tests import factories


@ddt.ddt
class RenderCredentialViewTests(SiteMixin, TestCase):
    faker = Faker()
    MOCK_USER_DATA = {
        "username": "test-user",
        "name": "Test User",
        "email": "test@example.org",
    }
    PROGRAM_NAME = "Fake PC"
    PROGRAM_TYPE = "Professional Certificate"
    CREDENTIAL_TITLE = "Fake Custom Credential Title"

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.course_certificates = [
            factories.CourseCertificateFactory.create(
                course_id=course_run.key, site=self.site, certificate_available_date="1994-05-11T03:14:01Z"
            )
            for course_run in self.course_runs
        ]
        self.program = ProgramFactory(title="TestProgram1", course_runs=self.course_runs, site=self.site)
        self.program_certificate = factories.ProgramCertificateFactory(
            site=self.site,
            program_uuid=self.program.uuid,
            program=self.program,
        )
        self.program_certificate.program = self.program
        self.program_certificate.save()
        self.signatory_1 = factories.SignatoryFactory()
        self.signatory_2 = factories.SignatoryFactory()
        self.program_certificate.signatories.add(self.signatory_1, self.signatory_2)
        self.user_credential = factories.UserCredentialFactory(
            username=self.MOCK_USER_DATA["username"], credential=self.program_certificate
        )
        self.course_user_credentials = [
            factories.UserCredentialFactory.create(
                username=self.MOCK_USER_DATA["username"],
                credential=course_cert,
            )
            for course_cert in self.course_certificates
        ]
        self.platform_name = self.site.siteconfiguration.platform_name
        user = UserFactory(username=self.MOCK_USER_DATA["username"])
        self.client.login(username=user.username, password=USER_PASSWORD)

    def _render_user_credential(
        self,
        use_proper_logo_url=True,
        user_credential=None,
        program_certificate=None,
        custom_orgs=None,
        test_user_data=None,
        expected_status_code=None,
    ):
        """Helper method to render a user certificate."""
        user_credential = user_credential or self.user_credential
        program_certificate = program_certificate or self.program_certificate
        program_uuid = program_certificate.program_uuid
        credential_title = program_certificate.title or self.PROGRAM_NAME
        expected_status_code = expected_status_code or 200

        if custom_orgs:
            organizations = custom_orgs
        else:
            organizations = [
                self._create_organization_details(use_proper_logo_url),
                self._create_organization_details(use_proper_logo_url),
            ]

        mocked_program_data = ProgramDetails(
            uuid=str(program_uuid),
            title=self.PROGRAM_NAME,
            type=self.PROGRAM_TYPE,
            type_slug=slugify(self.PROGRAM_TYPE),
            credential_title=credential_title,
            course_count=2,
            organizations=organizations,
            hours_of_effort=self.faker.pyint(),
            status="active",
        )

        with patch("credentials.apps.core.models.SiteConfiguration.get_user_api_data") as user_data, patch(
            "credentials.apps.credentials.models.ProgramCertificate.program_details", new_callable=PropertyMock
        ) as mock_program_details:
            user_data.return_value = test_user_data if test_user_data else self.MOCK_USER_DATA
            mock_program_details.return_value = mocked_program_data
            response = self.client.get(user_credential.get_absolute_url())
            self.assertEqual(response.status_code, expected_status_code)

        return response

    def _create_organization_details(self, use_proper_logo_url=True):
        """Helper method to create organization details."""
        return OrganizationDetails(
            uuid=str(uuid.uuid4()),
            key=self.faker.word(),
            name=self.faker.word(),
            display_name=self.faker.word(),
            certificate_logo_image_url=self.faker.url() if use_proper_logo_url else None,
        )

    def assert_matching_template_origin(self, actual, expected_template_name):
        expected = select_template([expected_template_name])
        self.assertEqual(actual.origin, expected.origin)

    @responses.activate
    def test_sharing_bar_with_anonymous_user(self):
        """Verify that the view renders certificate without sharing bar."""
        self.client.logout()
        response = self._render_user_credential()

        self.assertNotContains(response, "Print or share your certificate")

    @responses.activate
    def test_sharing_bar_with_staff_user(self):
        """Verify that the view renders certificate with sharing bar."""
        self.client.logout()
        staff_user = UserFactory(is_staff=True)
        self.client.login(username=staff_user.username, password=USER_PASSWORD)
        response = self._render_user_credential()

        self.assertContains(response, "Print or share your certificate")

    @responses.activate
    def test_awarded_with_logged_in_user(self):
        """Verify that the view renders awarded certificates with sharing bar."""
        response = self._render_user_credential()
        response_context_data = response.context_data

        # sharing bar
        self.assertContains(response, "Print or share your certificate")
        self.assertContains(response, "Print this certificate")

        self.assertContains(response=response, text=self.PROGRAM_NAME, count=2)
        self.assertNotContains(response=response, text=self.CREDENTIAL_TITLE)

        self.assertEqual(response_context_data["user_credential"], self.user_credential)
        self.assertEqual(response_context_data["user_data"], self.MOCK_USER_DATA)
        self.assertEqual(response_context_data["page_title"], self.PROGRAM_TYPE)
        self.assertEqual(response_context_data["program_name"], self.PROGRAM_NAME)

        actual_child_templates = response_context_data["child_templates"]
        expected_credential_template = "openedx/credentials/programs/{}/certificate.html".format(
            slugify(self.PROGRAM_TYPE)
        )
        self.assert_matching_template_origin(actual_child_templates["credential"], expected_credential_template)
        self.assert_matching_template_origin(actual_child_templates["footer"], "_footer.html")
        self.assert_matching_template_origin(actual_child_templates["header"], "_header.html")

    @ddt.data(
        (False, False, False),
        (False, False, True),
        (False, True, True),
        (True, True, True),
        (True, True, False),
    )
    @ddt.unpack
    @responses.activate
    def test_social_sharing_availability_site(self, facebook_sharing, twitter_sharing, linkedin_sharing):
        """
        Verify Facebook, Twitter and LinkedIn sharing availability for sites.
        """
        self.site_configuration.enable_facebook_sharing = facebook_sharing
        self.site_configuration.enable_twitter_sharing = twitter_sharing
        self.site_configuration.enable_linkedin_sharing = linkedin_sharing
        self.site_configuration.save()

        response = self._render_user_credential()
        response_context_data = response.context_data

        assert ("Facebook" in response.content.decode("utf-8")) == facebook_sharing
        assert ("Tweet" in response.content.decode("utf-8")) == twitter_sharing
        assert ("LinkedIn" in response.content.decode("utf-8")) == linkedin_sharing

        facebook_url = response_context_data.get("facebook_url", "")
        twitter_url = response_context_data.get("twitter_url", "")
        linkedin_url = response_context_data.get("linkedin_url", "")
        assert bool(facebook_url) == facebook_sharing
        assert bool(twitter_url) == twitter_sharing
        assert bool(linkedin_url) == linkedin_sharing

        # Basic sanity checking on the URLs: no template stubs or missing variables
        assert "={{" not in facebook_url
        assert "=&" not in facebook_url
        assert "={{" not in twitter_url
        assert "=&" not in twitter_url
        assert "={{" not in linkedin_url
        assert "=&" not in linkedin_url

    @responses.activate
    def test_awarded_with_custom_title(self):
        """Verify that the view renders a custom credential title if one is provided."""
        self.program_certificate.title = self.CREDENTIAL_TITLE
        self.program_certificate.save()

        response = self._render_user_credential()

        self.assertContains(response, "Print or share your certificate")
        self.assertNotContains(response=response, text=self.PROGRAM_NAME)
        self.assertContains(response=response, text=self.CREDENTIAL_TITLE, count=2)

    def test_revoked(self):
        """Verify that the view returns 404 when the uuid is valid but certificate status
        is 'revoked'.
        """
        self.user_credential.status = UserCredential.REVOKED
        self.user_credential.save()
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_invalid_uuid(self):
        """Verify that view returns 404 with invalid uuid."""
        path = reverse("credentials:render", kwargs={"uuid": uuid.uuid4().hex})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    @ddt.data((200, True), (404, False))
    @ddt.unpack
    @responses.activate
    def test_url_only_renders_on_correct_site(self, expected_return, is_same_site):
        """Verify that the view only renders an accessible URL if the credentials are from the
        site being rendered"""
        if is_same_site:
            site = self.site
            course_runs = self.course_runs
        else:
            domain = "unused.testsite"
            site_configuration = SiteConfigurationFactory(
                site__domain=domain,
            )
            site = site_configuration.site
            course = CourseFactory.create(site=site)
            course_runs = CourseRunFactory.create_batch(2, course=course)
        test_program = ProgramFactory(title="TestProgram2", course_runs=course_runs, site=site)
        test_program_certificate = factories.ProgramCertificateFactory(
            site=site,
            program_uuid=test_program.uuid,
            program=test_program,
        )
        test_signatory_1 = factories.SignatoryFactory()
        test_signatory_2 = factories.SignatoryFactory()
        test_program_certificate.signatories.add(test_signatory_1, test_signatory_2)
        test_user_credential = factories.UserCredentialFactory(
            username=self.MOCK_USER_DATA["username"], credential=test_program_certificate
        )
        response = self._render_user_credential(
            user_credential=test_user_credential,
            expected_status_code=expected_return,
        )
        self.assertEqual(response.status_code, expected_return)

    def test_invalid_credential(self):
        """Verify the view returns 404 for attempts to render unsupported credentials."""
        self.user_credential = factories.UserCredentialFactory(credential=factories.CourseCertificateFactory())
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    @override_switch("credentials.use_certificate_available_date", True)
    def test_future_certificate_available_date(self):
        """Verify that the view returns 404 when the uuid is valid but certificate is not yet visible."""
        self.course_certificates[0].certificate_available_date = "9999-05-11T03:14:01Z"
        self.course_certificates[0].save()
        response = self.client.get(self.user_credential.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    @override_switch("credentials.use_certificate_available_date", active=True)
    @responses.activate
    def test_no_certificate_available_date(self):
        """Verify that the view just returns normally when there isn't a valid_date attribute."""
        self.course_certificates[0].certificate_available_date = None
        self.course_certificates[0].save()
        self._render_user_credential()  # Will raise exception if not 200 status

    @override_switch("credentials.use_certificate_available_date", active=True)
    @responses.activate
    def test_visible_certificate_available_date(self):
        """Verify that the view renders the date at which the certificate is visible as the issue date."""
        response = self._render_user_credential()
        self.assertContains(response, "Issued May 1994")

    @responses.activate
    def test_signatory_organization_name_override(self):
        """Verify that the view response contain signatory organization name if signatory have organization."""
        self.signatory_1.organization_name_override = self.faker.word()
        self.signatory_1.save()
        response = self._render_user_credential()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.signatory_1.organization_name_override)
        self.assertNotContains(response, self.signatory_2.organization_name_override)

    @responses.activate
    def test_logo_missing_exception(self):
        with self.assertRaisesMessage(MissingCertificateLogoError, "No certificate image logo defined for program"):
            self._render_user_credential(use_proper_logo_url=False)

    @ddt.data((True, 'lang="es-419"'), (False, 'lang="en"'))
    @ddt.unpack
    @responses.activate
    def test_render_language(self, language_set, expected_text):
        """
        Verify that the view renders certificates in the configured language when it has been set,
        and in the default language (English) when content_language has not been set.
        """
        if language_set:
            ProgramCertificate.objects.update_or_create(
                program_uuid=self.program_certificate.program_uuid,
                defaults={"language": "es_419"},
                program=self.program,
            )
        response = self._render_user_credential()
        self.assertContains(response, expected_text)

    @ddt.data(1, 2, 3)
    @responses.activate
    def test_render_multiple_orgs(self, number_of_orgs):
        """
        Verify that the view renders certificates correctly with one, two, or
        three organizations.
        """
        orgs = [self._create_organization_details() for n in range(number_of_orgs)]
        response = self._render_user_credential(custom_orgs=orgs)

        if number_of_orgs == 1:
            self.assertEqual(response.context_data["org_name_string"], orgs[0].display_name)
        elif number_of_orgs == 2:
            self.assertEqual(
                response.context_data["org_name_string"], "{} and {}".format(orgs[0].display_name, orgs[1].display_name)
            )
        elif number_of_orgs == 3:
            self.assertEqual(
                response.context_data["org_name_string"],
                "{}, {}, and {}".format(orgs[0].display_name, orgs[1].display_name, orgs[2].display_name),
            )

    def test_render_verified_name(self):
        """
        Verify that the view renders certificates correctly if the user choose
        their verified name to be used on certificates
        """
        user_data = {
            "name": "John Doe",
            "verified_name": "Jonathan Doe",
            "use_verified_name_for_certs": True,
        }
        response = self._render_user_credential(test_user_data=user_data)
        self.assertContains(response, user_data["verified_name"])


class RenderExampleCredentialViewTests(SiteMixin, TestCase):
    faker = Faker()
    MOCK_USER_DATA = {
        "username": "test-user",
        "name": "Test User",
        "email": "test@example.org",
    }
    MOCK_STAFF_USER_DATA = {
        "username": "staff-test-user",
        "name": "Staff User",
        "email": "staff@example.org",
    }
    PROGRAM_NAME = "Fake PC"
    PROGRAM_TYPE = "Professional Certificate"
    CREDENTIAL_TITLE = "Fake Custom Credential Title"

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(site=self.site)
        self.course_runs = CourseRunFactory.create_batch(2, course=self.course)
        self.program = ProgramFactory(title="TestProgram1", course_runs=self.course_runs, site=self.site)
        self.program = ProgramFactory(title="TestProgram1", course_runs=self.course_runs, site=self.site)
        self.program_certificate = factories.ProgramCertificateFactory(
            site=self.site, program=self.program, program_uuid=self.program.uuid
        )
        self.signatory_1 = factories.SignatoryFactory()
        self.signatory_2 = factories.SignatoryFactory()
        self.platform_name = self.site.siteconfiguration.platform_name

        self.user = UserFactory(username=self.MOCK_USER_DATA["username"])
        self.staff_user = UserFactory(username=self.MOCK_STAFF_USER_DATA["username"], is_staff=True)

    def _create_organization_details(self, use_proper_logo_url=True):
        """Helper method to create organization details."""
        return OrganizationDetails(
            uuid=str(uuid.uuid4()),
            key=self.faker.word(),
            name=self.faker.word(),
            display_name=self.faker.word(),
            certificate_logo_image_url=self.faker.url() if use_proper_logo_url else None,
        )

    def _render_user_credential(
        self,
        test_user_data,
        use_proper_logo_url=True,
    ):
        """Helper method to render a user certificate."""
        program_certificate = self.program_certificate
        organizations = [
            self._create_organization_details(use_proper_logo_url),
            self._create_organization_details(use_proper_logo_url),
        ]

        mocked_program_data = ProgramDetails(
            uuid=str(self.program_certificate.program_uuid),
            title=self.PROGRAM_NAME,
            type=self.PROGRAM_TYPE,
            type_slug=slugify(self.PROGRAM_TYPE),
            credential_title=program_certificate.title,
            course_count=2,
            organizations=organizations,
            hours_of_effort=self.faker.pyint(),
            status="active",
        )

        with patch("credentials.apps.core.models.SiteConfiguration.get_user_api_data") as user_data, patch(
            "credentials.apps.credentials.models.ProgramCertificate.program_details", new_callable=PropertyMock
        ) as mock_program_details:
            user_data.return_value = test_user_data
            mock_program_details.return_value = mocked_program_data
            response = self.client.get(program_certificate.get_absolute_url())

        return response

    def testStaffUserRequired(self):
        self.client.login(username=self.staff_user.username, password=USER_PASSWORD)
        response = self._render_user_credential(test_user_data=self.MOCK_STAFF_USER_DATA)
        assert response.status_code == 200

        self.client.logout()
        response = self._render_user_credential(test_user_data={})
        assert response.status_code != 200

        self.client.login(username=self.user.username, password=USER_PASSWORD)
        response = self._render_user_credential(test_user_data=self.MOCK_USER_DATA)
        assert response.status_code != 200


@ddt.ddt
class ExampleCredentialTests(SiteMixin, TestCase):
    def test_get(self):
        """Verify the view renders a credential."""
        response = self.client.get(reverse("credentials:example"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get("{}?program_type=professional-certificate".format(reverse("credentials:example")))
        self.assertEqual(response.status_code, 200)


class I18nAssetsTemplateTagTest(TestCase):
    def test_construct_file_language_names(self):
        """Verify that the method for constructing file paths properly creates the set"""
        filepath = "some/test/path.svg"

        # Verify that for two different, full language codes all paths are generated, including the 2 characters ones
        language = "es-419"
        default = "en-US"
        paths = i18n_assets.construct_file_language_names(filepath, language, default)
        self.assertEqual(
            paths,
            [
                "some/test/path-es-419.svg",
                "some/test/path-es.svg",
                "some/test/path-en-US.svg",
                "some/test/path-en.svg",
                "some/test/path.svg",
            ],
        )

        # Verify that for two identical, 2 character language codes, only that path and the default is generated
        language = "en"
        default = "en"
        paths = i18n_assets.construct_file_language_names(filepath, language, default)
        self.assertEqual(
            paths,
            [
                "some/test/path-en.svg",
                "some/test/path.svg",
            ],
        )

    def test_translate_file_path_filter(self):
        """Verify that the filter correctly filters an image"""

        context = Context({})
        template = "{% load i18n_assets %}" + '{{ "openedx/images/example-logo.svg" | translate_file_path}}'
        template_to_render = Template(template)
        rendered_template = template_to_render.render(context)
        # Make sure the translated string occurs in the template
        self.assertEqual(rendered_template.find("openedx/images/example-logo-en.svg"), 0)
