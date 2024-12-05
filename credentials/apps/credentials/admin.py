from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin
from django.db.models import Q

from credentials.apps.credentials.forms import ProgramCertificateAdminForm, SignatoryModelForm
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    ProgramCompletionEmailConfiguration,
    RevokeCertificatesConfig,
    Signatory,
    UserCredential,
    UserCredentialAttribute,
    UserCredentialDateOverride,
)


class TimeStampedModelAdminMixin:
    readonly_fields = (
        "created",
        "modified",
    )


class UserCredentialAttributeInline(admin.TabularInline):
    model = UserCredentialAttribute
    extra = 1


class UserCredentialDateOverrideInline(admin.TabularInline):
    model = UserCredentialDateOverride
    readonly_fields = ("date",)
    can_delete = False


@admin.register(UserCredential)
class UserCredentialAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ("username", "certificate_uuid", "status", "credential_content_type", "title")
    list_filter = ("status", "credential_content_type")
    readonly_fields = TimeStampedModelAdminMixin.readonly_fields + ("uuid",)
    search_fields = ("username",)
    inlines = (UserCredentialAttributeInline, UserCredentialDateOverrideInline)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("credential")

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

        matching_program_certs = ProgramCertificate.objects.filter(program__title__icontains=search_term).values_list(
            "id", flat=True
        )
        matching_course_run_certs = CourseCertificate.objects.filter(
            Q(course_run__title_override__icontains=search_term) | Q(course_run__course__title__icontains=search_term)
        ).values_list("id", flat=True)

        matching_titles_qs = UserCredential.objects.filter(
            Q(program_credentials__in=matching_program_certs) | Q(course_credentials__in=matching_course_run_certs)
        )

        queryset |= matching_titles_qs
        return queryset, use_distinct


@admin.register(CourseCertificate)
class CourseCertificateAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ("course_id", "certificate_type", "site", "is_active")
    list_filter = ("certificate_type", "is_active")
    readonly_fields = ("certificate_available_date",)
    autocomplete_fields = ("course_run",)
    search_fields = ("course_id",)


@admin.register(ProgramCertificate)
class ProgramCertificateAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    form = ProgramCertificateAdminForm
    list_display = ("program_uuid", "site", "is_active", "program")
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


@admin.register(RevokeCertificatesConfig)
class RevokeCertificatesConfigAdmin(ConfigurationModelAdmin):
    pass
