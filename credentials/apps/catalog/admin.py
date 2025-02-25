from django.contrib import admin

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "uuid", "title")
    list_filter = ("site",)
    readonly_fields = ("id", "key", "uuid", "title", "owners", "site")
    search_fields = ("id", "key", "title", "uuid")


@admin.register(CourseRun)
class CourseRunAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "uuid", "title_override", "start_date", "end_date")
    readonly_fields = ("id", "key", "uuid", "title_override", "start_date", "end_date", "course")
    search_fields = ("id", "key", "title_override", "uuid", "course__title")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "uuid", "type")
    list_filter = ("site",)
    readonly_fields = (
        "title",
        "uuid",
        "type",
        "course_runs",
        "site",
        "authoring_organizations",
        "type_slug",
        "total_hours_of_effort",
        "status",
    )
    search_fields = ("title", "uuid")


@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ("name", "org_name", "pathway_type", "status", "email", "uuid")
    list_filter = ("site", "status")
    readonly_fields = ("name", "org_name", "pathway_type", "email", "uuid", "site", "programs")
    search_fields = ("name", "uuid")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "uuid")
    list_filter = ("site",)
    readonly_fields = ("name", "key", "uuid", "site", "certificate_logo_image_url")
    search_fields = ("name", "key", "uuid")
