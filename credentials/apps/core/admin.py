""" Admin configuration for core models. """

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from credentials.apps.core.forms import SiteConfigurationAdminForm
from credentials.apps.core.models import SiteConfiguration, User


class ChangeUserStatusAdminMixin:
    """
    Provides bulk actions to change the user status on boolean toggles:

    * activate_selected, deactivate_selected
    * add_is_staff_to_selected, remove_is_staff_from_selected
    * add_is_superuser_to_selected, remove_is_superuser_from_selected
    """

    @admin.action(description=_("Activate selected entries"))
    def activate_selected(self: admin.ModelAdmin, request, queryset):
        """Activate the selected entries."""
        count = queryset.count()
        queryset.update(is_active=True)
        model_name = self.__class__.__name__

        if count == 1:
            message = _("1 {model_name} entry was successfully activated.")
        else:
            message = _("{count} {model_name} entries were successfully activated.")
        message = message.format(count=count, model_name=model_name)
        self.message_user(request, message)

    @admin.action(description=_("Deactivate selected entries"))
    def deactivate_selected(self: admin.ModelAdmin, request, queryset):
        """Deactivate the selected entries."""
        count = queryset.count()
        queryset.update(is_active=False)
        model_name = self.__class__.__name__

        if count == 1:
            message = _("1 {model_name} entry was successfully deactivated.")
        else:
            message = _("{count} {model_name} entries were successfully deactivated.")
        message = message.format(count=count, model_name=model_name)
        self.message_user(request, message)

    @admin.action(description=_("Add is_staff to selected entries"))
    def add_is_staff_to_selected(self: admin.ModelAdmin, request, queryset):
        """Add is_staff to selected entries."""
        count = queryset.count()
        queryset.update(is_staff=True)
        model_name = self.__class__.__name__

        if count == 1:
            message = _("1 {model_name} entry was successfully changed.")
        else:
            message = _("{count} {model_name} entries were successfully changed.")
        message = message.format(count=count, model_name=model_name)
        self.message_user(request, message)

    @admin.action(description=_("Remove is_staff from selected entries"))
    def remove_is_staff_from_selected(self: admin.ModelAdmin, request, queryset):
        """Remove is_staff from selected entries."""
        count = queryset.count()
        queryset.update(is_staff=False)
        model_name = self.__class__.__name__

        if count == 1:
            message = _("1 {model_name} entry was successfully changed.")
        else:
            message = _("{count} {model_name} entries were successfully changed.")
        message = message.format(count=count, model_name=model_name)
        self.message_user(request, message)

    @admin.action(description=_("Add is_superuser to selected entries"))
    def add_is_superuser_to_selected(self: admin.ModelAdmin, request, queryset):
        """Add is_superuser to selected entries."""
        count = queryset.count()
        queryset.update(is_superuser=True)
        model_name = self.__class__.__name__

        if count == 1:
            message = _("1 {model_name} entry was successfully changed.")
        else:
            message = _("{count} {model_name} entries were successfully changed.")
        message = message.format(count=count, model_name=model_name)
        self.message_user(request, message)

    @admin.action(description=_("Remove is_superuser from selected entries"))
    def remove_is_superuser_from_selected(self: admin.ModelAdmin, request, queryset):
        """Remove is_superuser from selected entries."""
        count = queryset.count()
        queryset.update(is_superuser=False)
        model_name = self.__class__.__name__
        WARNING = (
            "NOTE: This only toggles the is_superuser status flag. "
            "If the user remains active you will need to manually "
            "remove them from permission groups."
        )

        if count == 1:
            message = _("1 {model_name} entry was successfully changed.")
        else:
            message = _("{count} {model_name} entries were successfully changed.")
        message = message.format(count=count, model_name=model_name)
        self.message_user(request, message)
        self.message_user(request, WARNING, level=messages.WARNING)


@admin.register(User)
class CustomUserAdmin(ChangeUserStatusAdminMixin, UserAdmin):
    """Admin configuration for the custom User model."""

    actions = [
        "activate_selected",
        "deactivate_selected",
        "add_is_staff_to_selected",
        "remove_is_staff_from_selected",
        "add_is_superuser_to_selected",
        "remove_is_superuser_from_selected",
    ]
    list_display = ("username", "email", "full_name", "first_name", "last_name", "is_staff")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("full_name", "first_name", "last_name", "email")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin for the SiteConfiguration model."""

    list_display = ("site", "lms_url_root")
    search_fields = ("site__name",)
    form = SiteConfigurationAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "site",
                    "platform_name",
                    "company_name",
                    "segment_key",
                    "theme_name",
                    "partner_from_address",
                    "records_enabled",
                )
            },
        ),
        (
            _("URLs"),
            {
                "fields": (
                    "lms_url_root",
                    "catalog_api_url",
                    "tos_url",
                    "privacy_policy_url",
                    "homepage_url",
                    "verified_certificate_url",
                    "certificate_help_url",
                    "records_help_url",
                )
            },
        ),
        (
            _("Social Sharing"),
            {
                "fields": (
                    "facebook_app_id",
                    "twitter_username",
                    "enable_facebook_sharing",
                    "enable_linkedin_sharing",
                    "enable_twitter_sharing",
                )
            },
        ),
    )
