"""Tests for Credentials fixtures."""
from django.core.management import call_command
from django.test import TestCase


class TestCredentialsFixtures(TestCase):
    """ Tests preventing credentials fixtures from going stale."""

    def test_sample_data_fixture(self):
        """ Verify that installation of fixture will fail if the credentials
        schema is altered.
        """
        call_command('loaddata', 'sample_data')
