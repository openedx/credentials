""" Tests for records models """

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from credentials.apps.catalog.tests.factories import CourseRunFactory, PathwayFactory, ProgramFactory
from credentials.apps.records.tests.factories import (
    ProgramCertRecordFactory,
    UserCreditPathwayFactory,
    UserGradeFactory,
)
from credentials.shared.constants import PathwayType


class UserGradeTests(TestCase):
    """Tests for UserGrade model"""

    def test_protected_deletion(self):
        course_run = CourseRunFactory()
        UserGradeFactory(course_run=course_run)
        with self.assertRaises(ProtectedError):
            course_run.delete()


class ProgramCertRecordTests(TestCase):
    """Tests for ProgramCertRecord model"""

    def test_protected_deletion(self):
        program = ProgramFactory()
        ProgramCertRecordFactory(program=program)
        with self.assertRaises(ProtectedError):
            program.delete()


class UserCreditPathwayTests(TestCase):
    """Tests for UserCreditPathway model"""

    def test_non_credit_pathway_validation(self):
        """Test that UserCreditPathway does not allow non-credit pathways."""
        for pathway_type in PathwayType:
            pathway = PathwayFactory(pathway_type=pathway_type.value)
            if pathway.pathway_type == PathwayType.CREDIT.value:
                try:
                    UserCreditPathwayFactory(pathway=pathway)
                except ValidationError:
                    self.fail("UserCreditPathway did not accept a credit pathway unexpectedly.")
            else:
                with self.assertRaises(ValidationError):
                    UserCreditPathwayFactory(pathway=pathway)

    def test_protected_deletion(self):
        pathway = PathwayFactory()
        UserCreditPathwayFactory(pathway=pathway)
        with self.assertRaises(ProtectedError):
            pathway.delete()
