""" Tests for records models """

from django.core.exceptions import ValidationError
from django.test import TestCase

from credentials.apps.catalog.tests.factories import PathwayFactory
from credentials.apps.records.tests.factories import UserCreditPathwayFactory
from credentials.shared.constants import PathwayType


class UserCreditPathwayTests(TestCase):
    """ Tests for UserCreditPathway model """

    def test_non_credit_pathway_validation(self):
        """ Test that UserCreditPathway does not allow non-credit pathways. """
        for pathway_type in PathwayType:
            pathway = PathwayFactory(pathway_type=pathway_type.value)
            if pathway.pathway_type == PathwayType.CREDIT.value:
                try:
                    UserCreditPathwayFactory(pathway=pathway)
                except ValidationError:
                    self.fail('UserCreditPathway did not accept a credit pathway unexpectedly.')
            else:
                with self.assertRaises(ValidationError):
                    UserCreditPathwayFactory(pathway=pathway)
