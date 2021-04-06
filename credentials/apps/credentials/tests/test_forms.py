import dataclasses
from unittest import mock

import factory
import faker
from django.test import TestCase

from credentials.apps.catalog.data import OrganizationDetails, ProgramDetails
from credentials.apps.core.tests.factories import SiteConfigurationFactory
from credentials.apps.credentials.forms import ProgramCertificateAdminForm
from credentials.apps.credentials.tests.factories import ProgramCertificateFactory


class ProgramCertificateAdminFormTests(TestCase):
    def test_program_uuid(self):
        """Verify a ValidationError is raised if the program's authoring organizations have
        no certificate images."""
        sc = SiteConfigurationFactory()
        data = factory.build(dict, FACTORY_CLASS=ProgramCertificateFactory)
        data["site"] = sc.site.id

        form = ProgramCertificateAdminForm(data)
        fake = faker.Faker()

        bad_organization = OrganizationDetails(
            uuid=fake.uuid4(),
            key=fake.word(),
            name=fake.word(),
            display_name=fake.word(),
            certificate_logo_image_url=None,
        )
        good_organization = dataclasses.replace(bad_organization, certificate_logo_image_url=fake.word())

        bad_program = ProgramDetails(
            uuid=fake.uuid4(),
            title=fake.word(),
            type=fake.word(),
            type_slug=fake.word(),
            credential_title=fake.word(),
            course_count=fake.random_digit(),
            organizations=[bad_organization],
            hours_of_effort=fake.random_digit(),
            status=fake.word(),
        )
        good_program = dataclasses.replace(bad_program, organizations=[good_organization])
        with mock.patch(
            "credentials.apps.credentials.forms.get_program_details_by_uuid", return_value=bad_program
        ) as mock_method:
            self.assertFalse(form.is_valid())
            mock_method.assert_called_with(data["program_uuid"], sc.site)
            self.assertEqual(
                form.errors["program_uuid"][0],
                "All authoring organizations of the program MUST have a certificate image defined!",
            )

        form = ProgramCertificateAdminForm(data)
        with mock.patch(
            "credentials.apps.credentials.forms.get_program_details_by_uuid", return_value=good_program
        ) as mock_method:
            self.assertFalse(form.is_valid())
            mock_method.assert_called_with(data["program_uuid"], sc.site)
            self.assertNotIn("program_uuid", form.errors)
