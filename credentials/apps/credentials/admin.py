from django.contrib import admin

from credentials.apps.credentials.forms import ProgramCertificateAdminForm, SignatoryModelForm
from credentials.apps.credentials.models import (
    CourseCertificate,
    ProgramCertificate,
    Signatory,
    UserCredential,
    UserCredentialAttribute,
)


class TimeStampedModelAdminMixin:
    readonly_fields = ('created', 'modified',)


class UserCredentialAttributeInline(admin.TabularInline):
    model = UserCredentialAttribute
    extra = 1


@admin.register(UserCredential)
class UserCredentialAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ('username', 'certificate_uuid', 'status', 'credential_content_type')
    list_filter = ('status', 'credential_content_type')
    readonly_fields = TimeStampedModelAdminMixin.readonly_fields + ('uuid',)
    search_fields = ('username',)
    inlines = (UserCredentialAttributeInline,)

    def certificate_uuid(self, obj):
        """Certificate UUID value displayed on admin panel."""
        return obj.uuid.hex


@admin.register(CourseCertificate)
class CourseCertificateAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    list_display = ('course_id', 'certificate_type', 'site', 'is_active')
    list_filter = ('certificate_type', 'is_active')
    search_fields = ('course_id',)


@admin.register(ProgramCertificate)
class ProgramCertificateAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    form = ProgramCertificateAdminForm
    list_display = ('program_uuid', 'site', 'is_active')
    list_filter = ('is_active', 'site',)
    search_fields = ('program_uuid', )

    def get_search_results(self, request, queryset, search_term):

        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term.replace('-', ''))

        return queryset, use_distinct


@admin.register(Signatory)
class SignatoryAdmin(TimeStampedModelAdminMixin, admin.ModelAdmin):
    form = SignatoryModelForm
    list_display = ('name', 'title', 'image')
    search_fields = ('name',)
