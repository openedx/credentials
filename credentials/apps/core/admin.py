""" Admin configuration for core models. """

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from credentials.apps.core.models import SiteConfiguration, User


class CustomUserAdmin(UserAdmin):
    """ Admin configuration for the custom User model. """
    list_display = ('username', 'email', 'full_name', 'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


class SiteConfigurationAdmin(admin.ModelAdmin):
    """ Admin for the SiteConfiguration model."""
    list_display = ('site', 'lms_url_root')
    search_fields = ('site__name',)


admin.site.register(User, CustomUserAdmin)
admin.site.register(SiteConfiguration, SiteConfigurationAdmin)
