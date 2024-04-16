"""
Core Admin Module Test Cases
"""

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest
from django.test import TestCase

from credentials.apps.core.admin import CustomUserAdmin
from credentials.apps.core.models import User
from credentials.apps.core.tests.factories import USER_PASSWORD, UserFactory


class UsersAdminTestCase(TestCase):
    """
    Test Case module for Users Admin
    """

    def setUp(self):
        super().setUp()
        self.user1 = UserFactory(
            lms_user_id=1,
            is_active=True,
            is_superuser=False,
            is_staff=False,
        )
        self.user2 = UserFactory(
            lms_user_id=2,
            is_active=True,
            is_superuser=False,
            is_staff=False,
        )
        self.superuser = UserFactory(lms_user_id=3, is_superuser=True, is_staff=True)
        self.user_admin = CustomUserAdmin(self.superuser, AdminSite())

        self.request = HttpRequest()
        self.request.session = "session"
        self.request.user = self.superuser
        self.request._messages = FallbackStorage(self.request)  # pylint: disable=protected-access
        self.client.login(username=self.superuser.username, password=USER_PASSWORD)

    def test_user_actions(self):
        """
        user should have its custom actions.
        """
        actions = self.user_admin.get_actions(self.request)
        assert "delete_selected" in actions
        assert "activate_selected" in actions
        assert "deactivate_selected" in actions
        assert "add_is_staff_to_selected" in actions
        assert "remove_is_staff_from_selected" in actions
        assert "add_is_superuser_to_selected" in actions
        assert "remove_is_superuser_from_selected" in actions

    def test_deactivate_selected_should_deactivate_active_users(self):
        """
        action deactivate_selected should deactivate users, and only
        the selected users
        """
        queryset = User.objects.filter(lms_user_id__in=[1, 2])
        self.user_admin.deactivate_selected(self.request, queryset)
        assert not User.objects.get(lms_user_id=1).is_active
        assert not User.objects.get(lms_user_id=2).is_active
        assert User.objects.get(lms_user_id=3).is_active

    def test_activate_selected_should_activate_active_users(self):
        """
        action activate_selected should activate users.
        """
        queryset = User.objects.filter(lms_user_id__in=[1, 2])
        # first deactivate the test accounts
        self.user_admin.deactivate_selected(self.request, queryset)

        self.user_admin.activate_selected(self.request, queryset)
        assert User.objects.get(lms_user_id=1).is_active
        assert User.objects.get(lms_user_id=2).is_active

    def test_add_is_staff_to_selected_should_modify_users(self):
        """
        action add_is_staff_to_selected should toggle the attribute on for
        selected users
        """
        queryset = User.objects.filter(lms_user_id__in=[1, 2])
        self.user_admin.add_is_staff_to_selected(self.request, queryset)
        assert User.objects.get(lms_user_id=1).is_staff
        assert User.objects.get(lms_user_id=2).is_staff

    def test_remove_is_staff_from_selected_should_modify_users(self):
        """
        action remove_is_staff_from_selected should toggle the attribute off for
        selected users
        """
        queryset = User.objects.filter(lms_user_id__in=[1, 2])
        self.user_admin.remove_is_staff_from_selected(self.request, queryset)
        assert not User.objects.get(lms_user_id=1).is_staff
        assert not User.objects.get(lms_user_id=2).is_staff
        assert User.objects.get(lms_user_id=3).is_staff

    def test_add_is_superuser_to_selected_should_modify_users(self):
        """
        action add_is_superuser_to_selected should toggle the attribute on for
        selected users
        """
        queryset = User.objects.filter(lms_user_id__in=[1, 2])
        self.user_admin.add_is_superuser_to_selected(self.request, queryset)
        assert User.objects.get(lms_user_id=1).is_superuser
        assert User.objects.get(lms_user_id=2).is_superuser

    def test_remove_is_superuser_from_selected_should_modify_users(self):
        """
        action remove_is_superuser_from_selected should toggle the attribute off for
        selected users
        """
        queryset = User.objects.filter(lms_user_id__in=[1, 2])
        self.user_admin.remove_is_superuser_from_selected(self.request, queryset)
        assert not User.objects.get(lms_user_id=1).is_superuser
        assert not User.objects.get(lms_user_id=2).is_superuser
        assert User.objects.get(lms_user_id=3).is_superuser
