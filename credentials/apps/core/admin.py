""" Admin configuration for core models. """

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from credentials.apps.core.forms import SiteConfigurationAdminForm
from credentials.apps.core.models import SiteConfiguration, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for the custom User model."""

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


