""" Admin configuration for records models. """

from django.contrib import admin

from credentials.apps.records.models import UserGrade


@admin.register(UserGrade)
class UserGradeAdmin(admin.ModelAdmin):
    """ Admin for the UserGrade model."""
    list_display = ('username', 'course_run', 'letter_grade', 'percent_grade',)
    search_fields = ('username', 'course_run__key', 'mode',)
    raw_id_fields = ('course_run',)
