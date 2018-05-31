""" Admin configuration for records models. """

from django.contrib import admin

from credentials.apps.records.models import UserGrade


@admin.register(UserGrade)
class UserGradeAdmin(admin.ModelAdmin):
    """ Admin for the UserGrade model."""
    list_display = ('user', 'course_run', 'letter_grade', 'percent_grade',)
    search_fields = ('user__username', 'course_run__key', 'mode',)
    raw_id_fields = ('user', 'course_run',)
