"""
Tests for the Python functions in the Core app's `api.py` file
"""

import ddt
from django.test import TestCase
from openedx_events.learning.data import UserData, UserPersonalData
from testfixtures import LogCapture

from credentials.apps.core.api import get_or_create_user_from_event_data, get_user_by_username
from credentials.apps.core.tests.factories import UserFactory


@ddt.ddt
class CoreApiTests(TestCase):
    """
    Unit tests for `api.py` functions in the Core Django app
    """

    def test_get_user_by_username(self):
        user = UserFactory()

        retrieved_user = get_user_by_username(user.username)
        assert retrieved_user.id == user.id

    def test_get_user_by_username_user_dne(self):
        retrieved_user = get_user_by_username("mistadobalina")
        assert retrieved_user is None

    def test_get_existing_user_from_event_data(self):
        """
        Test case to verify the behavior of the `get_or_create_user_from_event_bus_data` function when trying to
        retrieve a user that already exists in the system. Verifies that the user returned is the one we expected.
        """
        user = UserFactory()
        user_event_data = UserData(
            pii=UserPersonalData(
                username=user.username,
                email=user.email,
                name=user.full_name,
            ),
            id=user.lms_user_id,
            is_active=user.is_active,
        )

        returned_user, created = get_or_create_user_from_event_data(user_event_data)
        assert not created
        assert returned_user.username == user.username
        assert returned_user.email == user.email
        assert returned_user.full_name == user.full_name
        assert returned_user.lms_user_id == user.lms_user_id
        assert returned_user.is_active == user.is_active

    def test_create_new_user_from_event_data(self):
        """
        Test case to verify the behavior of the `get_or_create_user_from_event_bus_data` function when trying to
        retrieve a user that doesn't exist in Credentials. Verifies the user creation process.
        """
        new_user_event_data = UserData(
            pii=UserPersonalData(username="uginislame", email="coolperson@yup.com", name="Nicol Bolas"),
            id=123456789,
            is_active=True,
        )

        user, created = get_or_create_user_from_event_data(new_user_event_data)
        assert created
        assert user.username == "uginislame"
        assert user.email == "coolperson@yup.com"
        assert user.full_name == "Nicol Bolas"
        assert user.lms_user_id == 123456789
        assert user.is_active

    @ddt.data(None, True)
    def test_get_user_no_user_data_in_event_data(self, bad_data):
        """
        Test case to verify the behavior of the `get_or_create_user_from_event_bus_data` function when passed unexpected
        data.
        """
        expected_message = "Received null or unexpected data type when attempting to retrieve User information"

        with LogCapture() as log:
            get_or_create_user_from_event_data(bad_data)

        assert log.records[0].msg == expected_message
