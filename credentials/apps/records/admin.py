"""Admin configuration for records models."""

from django.contrib import admin

from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway, UserGrade


@admin.register(ProgramCertRecord)
class ProgramCertRecordAdmin(admin.ModelAdmin):
    """Admin for the ProgramCertRecord model."""

    list_display = (
        "uuid",
        "program",
        "user",
    )
    search_fields = (
        "uuid",
        "program__title",
        "user__username",
    )
    raw_id_fields = (
        "program",
        "user",
    )
    exclude = ("certificate",)


@admin.register(UserGrade)
class UserGradeAdmin(admin.ModelAdmin):
    """Admin for the UserGrade model."""

    list_display = (
        "username",
        "course_run",
        "letter_grade",
        "percent_grade",
    )
    search_fields = (
        "username",
        "course_run__key",
    )
    raw_id_fields = ("course_run",)
    readonly_fields = ["lms_last_updated_at"]


@admin.register(UserCreditPathway)
class UserCreditPathwayAdmin(admin.ModelAdmin):
    """Admin for UserCreditPathway"""

    list_display = (
        "user",
        "pathway",
        "program",
        "status",
    )
    search_fields = (
        "user__username",
        "pathway__org_name",
        "program_title",
        "status",
    )
    raw_id_fields = ("user", "pathway", "program")
