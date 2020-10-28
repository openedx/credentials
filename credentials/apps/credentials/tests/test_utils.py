import datetime

import ddt
from django.contrib.auth import get_user_model
from django.test import TestCase

from credentials.apps.credentials.utils import datetime_from_visible_date, validate_duplicate_attributes


User = get_user_model()


@ddt.ddt
class CredentialsUtilsTests(TestCase):
    """ Tests for credentials.utils methods """

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

    def test_datetime_from_visible_date(self):
        """ Verify that we convert LMS dates correctly. """
        self.assertIsNone(datetime_from_visible_date(''))
        self.assertIsNone(datetime_from_visible_date('2018-07-31'))
        self.assertIsNone(datetime_from_visible_date('2018-07-31T09:32:46+00:00'))  # should be Z for timezone
        self.assertEqual(datetime_from_visible_date('2018-07-31T09:32:46Z'),
                         datetime.datetime(2018, 7, 31, 9, 32, 46, tzinfo=datetime.timezone.utc))
