""" Admin configuration for core models. """

from django.contrib import admin

from credentials.apps.catalog.models import Course, CourseRun, Organization, Program


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


admin.site.register(Course, CourseAdmin)
admin.site.register(CourseRun, CourseRunAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Program, ProgramAdmin)
