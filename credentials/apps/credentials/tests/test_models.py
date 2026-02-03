"""Test models for credentials service app."""

import uuid
from dataclasses import dataclass
from unittest import mock

import ddt
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import slugify
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from credentials.apps.catalog.data import OrganizationDetails, ProgramDetails
from credentials.apps.catalog.tests.factories import CourseRunFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials import constants
from credentials.apps.credentials.exceptions import NoMatchingProgramException
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCompletionEmailConfiguration,
    Signatory,
    UserCredential,
)
from credentials.apps.credentials.tests.factories import (
    ProgramCertificateFactory,
    SignatoryFactory,
    UserCredentialFactory,
)
from credentials.settings.base import MEDIA_ROOT

TEST_DATA_ROOT = MEDIA_ROOT + "/test/data/"


class SignatoryTests(TestCase):
    """Test Signatory model."""

    def get_image(self, name):
        """Get one of the test images from the test data directory."""
        return ImageFile(open(TEST_DATA_ROOT + name + ".png"))  # pylint: disable=unspecified-encoding

    def create_clean(self, file_obj):
        """
        Shortcut to create a Signatory with a specific file.
        """
        Signatory(name="test_signatory", title="Test Signatory", image=file_obj).full_clean()

    def test_good_image(self):
        """Verify that saving a valid signatory image is no problem."""
        good_image = self.get_image("good")
        Signatory(name="test_signatory", title="Test Signatory", image=good_image).full_clean()

    def test_large_image(self):
        """Upload of large image size should raise validation exception."""
        large_image = self.get_image("large")
        self.assertRaises(ValidationError, self.create_clean, large_image)

    def test_signatory_file_saving(self):
        """
        Verify that asset file is saving with actual name and on correct path.
        """
        image = SimpleUploadedFile("image.jpg", b"file contents!")
        signatory = Signatory.objects.create(name="test name", title="Test Signatory", image=image)

        assert signatory.image.name.startswith("signatories/1/image")
        assert signatory.image.name.endswith(".jpg")

        # Now replace the asset with another file
        signatory.image = SimpleUploadedFile("image_2.jpg", b"file contents")
        signatory.save()

        assert signatory.image.name.startswith("signatories/1/image_2")
        assert signatory.image.name.endswith(".jpg")

    def test_str(self):
        """Verify the method serializes the Signatory's name and title."""
        signatory = SignatoryFactory()
        self.assertEqual(str(signatory), signatory.name + ", " + signatory.title)


class CourseCertificateTests(SiteMixin, TestCase):
    """Test Course Certificate model."""

    def setUp(self):
        super().setUp()
        self.course_key = CourseLocator(org="test", course="test", run="test")

    def test_invalid_course_key(self):
        """Test Validation Error occurs for invalid course key."""
        course_run = CourseRunFactory()

        with self.assertRaises(ValidationError) as context:
            CourseCertificate(
                site=self.site,
                is_active=True,
                course_id="test_invalid",
                certificate_type=constants.CertificateType.HONOR,
                course_run=course_run,
            ).full_clean()

        self.assertEqual(context.exception.message_dict, {"course_id": ["Invalid course key."]})


@ddt.ddt
class ProgramCertificateTests(SiteMixin, TestCase):
    """Tests for the ProgramCertificate model."""

    def test_str(self):
        instance = ProgramCertificateFactory()
        self.assertEqual(str(instance), "ProgramCertificate: " + str(instance.program_uuid))

    @ddt.data(
        (True, None),
        (True, "Test custom credential title"),
        (False, None),
        (False, "Other very special credential title"),
    )
    @ddt.unpack
    def test_program_details(self, use_org_name, credential_title):
        """Verify the method returns the details of program associated with the ProgramCertificate."""
        program_certificate = ProgramCertificateFactory(
            site=self.site, use_org_name=use_org_name, title=credential_title
        )
        program_uuid = program_certificate.program_uuid.hex
        courses = [
            {"key": "ACMEx/101x"},
            {"key": "FakeX/101x"},
        ]
        expected = ProgramDetails(
            uuid=program_uuid,
            title="Test Program",
            type="MicroFakers",
            type_slug=slugify("MicroFakers"),
            credential_title=credential_title,
            course_count=len(courses),
            organizations=[
                OrganizationDetails(
                    uuid=uuid.uuid4().hex,
                    key="ACMEx",
                    name="ACME University",
                    display_name="ACME University" if use_org_name else "ACMEx",
                    certificate_logo_image_url="http://example.com/acme.jpg",
                ),
                OrganizationDetails(
                    uuid=uuid.uuid4().hex,
                    key="FakeX",
                    name="Fake University",
                    display_name="Fake University" if use_org_name else "FakeX",
                    certificate_logo_image_url="http://example.com/fakex.jpg",
                ),
            ],
            hours_of_effort=None,
            status="active",
        )

        # Mocked at apps.credentials instead of apps.catalog because that's where it's being referenced
        with mock.patch("credentials.apps.credentials.models.get_program_details_by_uuid") as mock_program_get:
            mock_program_get.return_value = expected

            self.assertEqual(program_certificate.program_details, expected)
            mock_program_get.assert_called_with(uuid=program_certificate.program_uuid, site=program_certificate.site)

    def test_program_details_missing_program(self):
        """Test program details when there is no matching program"""
        program_certificate = ProgramCertificateFactory(site=self.site)
        # replace good UUID with new one
        program_certificate.program_uuid = uuid.uuid4()
        with self.assertRaises(NoMatchingProgramException):
            # attempt to access the program_details property
            program_certificate.program_details  # pylint: disable=pointless-statement


class UserCredentialTests(TestCase):
    def test_revoke(self):
        credential = UserCredentialFactory(status=UserCredential.AWARDED)
        self.assertEqual(credential.status, UserCredential.AWARDED)

        credential.revoke()
        self.assertEqual(credential.status, UserCredential.REVOKED)


@ddt.ddt
class ProgramCompletionEmailConfigurationTests(TestCase):
    def setUp(self):
        super().setUp()

        # Making a Program -like data model so we don't need to cross import. It quacks.
        @dataclass
        class FakeProgram:
            """Minimal fake Program -like data model for testing"""

            uuid: uuid.UUID
            type_slug: str

        self.fake_program = FakeProgram(uuid=uuid.uuid4(), type_slug="example-program-type")

        self.default_config = ProgramCompletionEmailConfiguration.objects.create(
            identifier="default",
            html_template="<h1>Default Template</h1>",
            plaintext_template="Default Template",
            enabled=False,
        )
        self.program_type_config = ProgramCompletionEmailConfiguration.objects.create(
            identifier=self.fake_program.type_slug,
            html_template="<h1>Program Type Template</h1>",
            plaintext_template="Program Type Template",
            enabled=False,
        )
        self.single_program_config = ProgramCompletionEmailConfiguration.objects.create(
            identifier=self.fake_program.uuid,
            html_template="<h1>Program Type Template</h1>",
            plaintext_template="Program Type Template",
            enabled=False,
        )

    @ddt.data(
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (True, False, False),
        (False, True, True),
        (False, True, False),
        (False, False, True),
        (False, False, False),
    )
    @ddt.unpack
    def test_get_email_config_for_program(self, default_exists, program_type_exists, single_program_exists):
        if not single_program_exists:
            self.single_program_config.delete()

        if not program_type_exists:
            self.program_type_config.delete()

        if not default_exists:
            self.default_config.delete()

        chosen_config = ProgramCompletionEmailConfiguration.get_email_config_for_program(
            self.fake_program.uuid, self.fake_program.type_slug
        )

        # Because we're using elifs we guarantee the item we're checking the most specific true value
        if single_program_exists:
            self.assertEqual(chosen_config, self.single_program_config)
        elif program_type_exists:
            self.assertEqual(chosen_config, self.program_type_config)
        elif default_exists:
            self.assertEqual(chosen_config, self.default_config)
        else:
            self.assertEqual(chosen_config, None)

    @ddt.data(
        ("This is a safe example", "This is a safe example"),
        (
            """This is an example with a <a href="http://example.com">link</a>""",
            """This is an example with a <a href="http://example.com">link</a>""",
        ),
        (
            """This is an example with a <script>alert("boo")</script>""",
            """This is an example with a &lt;script&gt;alert("boo")&lt;/script&gt;""",
        ),
        (
            """This has both <a href="http://example.com">links</a> and a <script>alert("boo")</script>""",
            """This has both <a href="http://example.com">links</a> and a &lt;script&gt;alert("boo")&lt;/script&gt;""",
        ),
    )
    @ddt.unpack
    def test_html_character_removal(self, input_value, expected_save_value):
        """Verifies that safe tags are kept and unsafe tags are cleaned"""
        self.default_config.html_template = input_value
        self.default_config.save()
        self.assertEqual(self.default_config.html_template, expected_save_value)
