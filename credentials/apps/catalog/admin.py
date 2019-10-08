from django.contrib import admin

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program

admin.site.register(Course)
admin.site.register(CourseRun)
admin.site.register(Organization)
admin.site.register(Pathway)
admin.site.register(Program)
