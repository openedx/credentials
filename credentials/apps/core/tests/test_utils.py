"""Test core.utils."""

from unittest import mock

from django.test import TestCase

from credentials.apps.core.tests.factories import UserFactory
from credentials.apps.core.utils import update_full_name


class UtilsTests(TestCase):
    """ Tests for the utility functions."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory(full_name='Bart')

    def test_update_full_name_no_user(self):
        # Just test that we don't blow up
        update_full_name(mock.MagicMock(), {})

    def test_update_full_name_no_full_name(self):
        # Just test that we don't blow up
        update_full_name(mock.MagicMock(), {}, self.user)

    def test_update_full_name_happy_path(self):
        strategy = mock.MagicMock()
        update_full_name(strategy, {'full_name': 'Bort'}, self.user)
        self.assertEqual(self.user.full_name, 'Bort')
        self.assertTrue(strategy.storage.user.changed.called)
