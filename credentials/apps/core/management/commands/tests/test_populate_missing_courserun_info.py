"""
Tests for the populate_missing_courserun_info management command
"""

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.test import TestCase

from credentials.apps.catalog.tests.factories import CourseRunFactory
from credentials.apps.core.tests.mixins import SiteMixin
from credentials.apps.credentials.models import CourseCertificate
from credentials.apps.credentials.tests.factories import CourseCertificateFactory


class CourseCertificateCourseRunSyncTests(SiteMixin, TestCase):
    def setUp(self):
        """
        Create the error condition:

        * A CourseRun
        * A CourseCertificate that has the key of the CourseRun in course_id,
          but doesn't have a FK to the CouseRun
        """
        super().setUp()
        self.course_run = CourseRunFactory()
        self.course_certificate = CourseCertificateFactory(course_id=self.course_run.key)

    def test_update_ids(self):
        """verify ids were updated"""
        with self.assertRaises(ObjectDoesNotExist):
            CourseCertificate.objects.get(course_run=self.course_run)

        call_command("populate_missing_courserun_info", verbose=True)

        course_cert = CourseCertificate.objects.get(course_run=self.course_run)
        self.assertEqual(course_cert.course_id, course_cert.course_run.key)

    def test_dry_run(self):
        """verify course_ids were NOT updated"""
        with self.assertRaises(ObjectDoesNotExist):
            CourseCertificate.objects.get(course_run=self.course_run)

        call_command(
            "populate_missing_courserun_info",
            verbose=True,
            dry_run=True,
        )

        with self.assertRaises(ObjectDoesNotExist):
            CourseCertificate.objects.get(course_run=self.course_run)
