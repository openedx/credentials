import ddt
from django.contrib.auth import get_user_model
from django.test import TestCase

from credentials.apps.credentials.utils import validate_duplicate_attributes

User = get_user_model()


@ddt.ddt
class ValidateDuplicateAttributesTests(TestCase):
    """ Tests for Validate the attributes method """

    def test_with_non_duplicate_attributes(self):
        """ Verify that the function will return True if no duplicated attributes found."""
        attributes = [
            {'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'},
            {'name': 'grade', 'value': '0.85'}
        ]
        self.assertTrue(validate_duplicate_attributes(attributes))

    def test_with_duplicate_attributes(self):
        """ Verify that the function will return False if duplicated attributes found."""

        attributes = [
            {'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'},
            {'name': 'whitelist_reason', 'value': 'Reason for whitelisting.'},
        ]

        self.assertFalse(validate_duplicate_attributes(attributes))
