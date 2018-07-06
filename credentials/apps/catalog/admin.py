""" Admin configuration for core models. """

from django.contrib import admin


class CourseAdmin(admin.ModelAdmin):
    """ Admin for the Course model."""
    list_display = ('key', 'title')
    search_fields = ('key', 'title', 'uuid')


class CourseRunAdmin(admin.ModelAdmin):
    """ Admin for the CourseRun model."""
    list_display = ('key', 'title')
    search_fields = ('key', 'title_override', 'course__title', 'uuid')


class OrganizationAdmin(admin.ModelAdmin):
    """ Admin for the Organization model."""
    list_display = ('key', 'name')
    search_fields = ('key', 'name', 'uuid')


class ProgramAdmin(admin.ModelAdmin):
    """ Admin for the Program model."""
    list_display = ('title', 'uuid')
    search_fields = ('title', 'uuid')
