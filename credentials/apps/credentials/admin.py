from django.contrib import admin

from credentials.apps.credentials.forms import ProgramCertificateAdminForm, SignatoryModelForm
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    ProgramCompletionEmailConfiguration,
    Signatory,
    UserCredential,
    UserCredentialAttribute,
)


class TimeStampedModelAdminMixin:
    readonly_fields = (
        "created",
        "modified",
    )


class UserCredentialAttributeInline(admin.TabularInline):
    model = UserCredentialAttribute
    extra = 1


@admin.register(UserCredential)
class UserCredentialAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ("username", "certificate_uuid", "status", "credential_content_type", "title")
    list_filter = ("status", "credential_content_type")
    readonly_fields = TimeStampedModelAdminMixin.readonly_fields + ("uuid",)
    search_fields = ("username",)
    inlines = (UserCredentialAttributeInline,)

    def certificate_uuid(self, obj):
        """Certificate UUID value displayed on admin panel."""
        return obj.uuid.hex

    def title(self, obj):
        """Retrieves the title of either the course or program that the certificate was awarded for"""
        if obj.credential_content_type.model_class() == ProgramCertificate:
            program = obj.credential.program
            if program:
                return program.title
        elif obj.credential_content_type.model_class() == CourseCertificate:
            course_run = obj.credential.course_run
            if course_run:
                return course_run.title
        return ""

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # TODO: add course queryset like program below to match course titles
        matching_program_title_qs = UserCredential.objects.filter(
            program_credentials__program__title__icontains=search_term
        )
        matching_course_run_title_qs = UserCredential.objects.filter(
            course_credentials__course_run__title_override__icontains=search_term
        )
        matching_course_title_qs = UserCredential.objects.filter(
            course_credentials__course_run__course__title__icontains=search_term
        )
        queryset = queryset | matching_program_title_qs | matching_course_run_title_qs | matching_course_title_qs
        return queryset, use_distinct


@admin.register(CourseCertificate)
class CourseCertificateAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ("course_id", "certificate_type", "site", "is_active")
    list_filter = ("certificate_type", "is_active")
    search_fields = ("course_id",)


@admin.register(ProgramCertificate)
class ProgramCertificateAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    form = ProgramCertificateAdminForm
    list_display = ("program_uuid", "site", "is_active")
    list_filter = (
        "is_active",
        "site",
    )
    autocomplete_fields = ("program",)
    search_fields = ("program_uuid", "program__title")

    def get_search_results(self, request, queryset, search_term):

        queryset, use_distinct = super().get_search_results(request, queryset, search_term.replace("-", ""))

        return queryset, use_distinct


@admin.register(Signatory)
class SignatoryAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    form = SignatoryModelForm
    list_display = ("name", "title", "image")
    search_fields = ("name",)


@admin.register(ProgramCompletionEmailConfiguration)
class ProgramCompletionEmailConfigurationAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ("identifier", "enabled")
    search_fields = ("identifier",)
