from django.contrib import admin

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('key', 'uuid', 'title')
    list_filter = ('site',)
    readonly_fields = ('uuid',)
    search_fields = ('key', 'title', 'uuid')


@admin.register(CourseRun)
class CourseRunAdmin(admin.ModelAdmin):
    list_display = ('key', 'uuid', 'title_override', 'start_date', 'end_date')
    readonly_fields = ('uuid',)
    search_fields = ('key', 'title_override', 'uuid')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'uuid', 'type')
    readonly_fields = ('uuid',)
    search_fields = ('title', 'uuid')


@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_name', 'pathway_type', 'email', 'uuid')
    readonly_fields = ('uuid',)
    search_fields = ('name', 'uuid')


admin.site.register(Organization)
