"""Tests for catalog models."""

from django.test import TestCase

from credentials.apps.catalog.tests.factories import CourseFactory, CourseRunFactory


class CourseRunTests(TestCase):
    """Course run tests."""

    def test_title(self):
        """Test that we gracefully provide a title override."""
        course = CourseFactory(title="Course Title")
        run_none = CourseRunFactory(title_override=None, course=course)
        run_overridden = CourseRunFactory(title_override="Run Title", course=course)

        self.assertEqual(run_none.title, "Course Title")
        self.assertEqual(run_overridden.title, "Run Title")
