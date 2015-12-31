"""
Tests for Issuer class.
"""
import ddt
from django.test import TestCase
from credentials.apps.credentials.utils import validate_duplicate_attributes


@ddt.ddt
class ValidateDuplicateAttributesTests(TestCase):
    """ Tests for Validate the attributes method """

    def test_with_non_duplicate_attributes(self):
        """ Verify that the method will return True if no duplicated attributes found."""
        attributes = [
            {"namespace": "whitelist1", "name": "grades1", "value": "0.9"},
            {"namespace": "whitelist2", "name": "grades2", "value": "0.7"}
        ]
        self.assertTrue(validate_duplicate_attributes(attributes))

    def test_with_duplicate_attributes(self):
        """ Verify that the method will return False if duplicated attributes found."""

        attributes = [
            {"namespace": "whitelist1", "name": "grades1", "value": "0.9"},
            {"namespace": "whitelist1", "name": "grades1", "value": "0.7"}
        ]

        self.assertFalse(validate_duplicate_attributes(attributes))
