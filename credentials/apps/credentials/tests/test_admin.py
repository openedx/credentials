"""
Credentials Admin Module Test Cases
"""

from unittest import mock

import factory
import faker
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse

from credentials.apps.catalog.data import OrganizationDetails, ProgramDetails
from credentials.apps.catalog.tests.factories import CourseRunFactory
from credentials.apps.core.tests.factories import USER_PASSWORD, SiteConfigurationFactory, UserFactory
from credentials.apps.credentials.forms import ProgramCertificateAdminForm
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    SignatoryFactory,
)


class ProgramCertificateAdminTestCase(TestCase):
    """
    Test Case module for ProgramCertificateAdmin
    """

    def setUp(self):
        super().setUp()
        self.superuser = UserFactory(lms_user_id=3, is_superuser=True, is_staff=True)

        self.request = HttpRequest()
        self.request.session = "session"
        self.request.user = self.superuser
        self.request._messages = FallbackStorage(self.request)  # pylint: disable=protected-access
        self.client.login(username=self.superuser.username, password=USER_PASSWORD)

        self.data = factory.build(dict, FACTORY_CLASS=ProgramCertificateFactory)
        self.sc = SiteConfigurationFactory()
        self.data["site"] = self.sc.site.id

        fake = faker.Faker()

        self.organization = OrganizationDetails(
            uuid=fake.uuid4(),
            key=fake.word(),
            name=fake.word(),
            display_name=fake.word(),
            certificate_logo_image_url=fake.word(),
        )

        self.program = ProgramDetails(
            uuid=fake.uuid4(),
            title=fake.word(),
            type=fake.word(),
            type_slug=fake.word(),
            credential_title=fake.word(),
            course_count=fake.random_digit(),
            organizations=[self.organization],
            hours_of_effort=fake.random_digit(),
            status=fake.word(),
        )

    def test_save_program_certificate_configuration_without_signatory_fails(self):
        """
        a ProgramCertificate configuration without a signatory fails validation
        """
        with mock.patch(
            "credentials.apps.credentials.forms.get_program_details_by_uuid", return_value=self.program
        ) as mock_method:
            admin_form = ProgramCertificateAdminForm(self.data)
            self.assertFalse(admin_form.is_valid())
            self.assertEqual(admin_form.errors["signatories"], ["This field is required."])
            mock_method.assert_called_with(self.data["program_uuid"], self.sc.site)


class CourseCertificateAdminTestCase(TestCase):
    """
    Test Case module for ProgramCertificateAdmin and CourseCertificateAdmin
    """

    def setUp(self):
        super().setUp()
        self.superuser = UserFactory(lms_user_id=3, is_superuser=True, is_staff=True)

        self.request = HttpRequest()
        self.request.session = "session"
        self.request.user = self.superuser
        self.request._messages = FallbackStorage(self.request)  # pylint: disable=protected-access
        self.client.login(username=self.superuser.username, password=USER_PASSWORD)

        self.signatory = SignatoryFactory()
        self.course_run = CourseRunFactory()

        # Create the data dictionary for the populated form fields
        self.data = factory.build(dict, FACTORY_CLASS=CourseCertificateFactory)
        # The factory creates a None CAD, but the admin (correctly) omits the key.
        self.data.pop("certificate_available_date", None)
        self.data["course_run"] = self.course_run.id
        self.data["course_id"] = self.course_run.key
        self.sc = SiteConfigurationFactory()
        self.data["site"] = self.sc.site.id

    def test_save_course_certificate_configuration_without_signatory_passes(self):
        """
        a CourseCertificate configuration without a signatory passes validation
        """
        expected = 302
        response = self.client.post(reverse("admin:credentials_coursecertificate_add"), data=self.data)
        self.assertEqual(response.status_code, expected)

    def test_save_course_certificate_configuration_with_signatory_passes(self):
        """
        a CourseCertificate configuration with a signatory passes validation
        """
        expected = 302
        data = self.data
        data["signatories"] = self.signatory.id
        response = self.client.post(reverse("admin:credentials_coursecertificate_add"), data=self.data)
        self.assertEqual(response.status_code, expected)
