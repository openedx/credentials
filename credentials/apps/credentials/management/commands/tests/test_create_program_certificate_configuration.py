"""
Tests for the create_program_certificate_configuration command
"""

from unittest import TestCase, mock

import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError

from credentials.apps.catalog.models import Program
from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.credentials.models import ProgramCertificate

COMMAND = "create_program_certificate_configuration"


@pytest.mark.django_db
class CertAllowlistGenerationTests(TestCase):
    """
    Tests for the create_credentials_api_configuration management command
    """

    def setUp(self):
        super().setUp()
        self.site = Site.objects.get(domain="example.com")
        new_course = CourseFactory.create(site=self.site)
        self.new_course_run = CourseRunFactory.create(course=new_course)
        self.orgs = [OrganizationFactory.create(name=name, site=self.site) for name in ["TestOrg1", "TestOrg2"]]

    def test_successful_generation(self):
        ProgramFactory.create(
            title="edX Demonstration Program",
            course_runs=[self.new_course_run],
            authoring_organizations=self.orgs,
            site=self.site,
        )
        call_command(command_name=COMMAND)
        assert len(ProgramCertificate.objects.all()) > 0

    def test_errors_when_demo_program_is_not_in_catalog(self):
        with pytest.raises(CommandError):
            call_command(command_name=COMMAND)
