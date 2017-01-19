"""
Django admin page for credential
"""
from django.contrib import admin

from credentials.apps.credentials.forms import SignatoryModelForm, ProgramCertificateAdminForm
from credentials.apps.credentials.models import (
    CertificateTemplate, CourseCertificate, CertificateTemplateAsset, ProgramCertificate, Signatory,
    UserCredentialAttribute, UserCredential
)


class UserCredentialAttributeInline(admin.TabularInline):
    """Tabular inline for the UserCredentialAttribute model."""
    model = UserCredentialAttribute
    extra = 1


class UserCredentialAdmin(admin.ModelAdmin):
    """Admin for the UserCredential model."""
    list_display = ('username', 'certificate_uuid', 'status', 'credential_content_type')
    list_filter = ('status', 'credential_content_type')
    search_fields = ('username',)
    readonly_fields = ('uuid',)
    inlines = (UserCredentialAttributeInline,)

    def certificate_uuid(self, obj):
        """Certificate UUID value displayed on admin panel."""
        return obj.uuid.hex


class CertificateTemplateAdmin(admin.ModelAdmin):
    """Admin for the CertificateTemplate model."""
    search_fields = ('name',)


class CertificateTemplateAssetAdmin(admin.ModelAdmin):
    """Admin for the CertificateTemplateAsset model."""
    list_display = ('name', 'asset_file')
    search_fields = ('name',)


class CourseCertificateAdmin(admin.ModelAdmin):
    """Admin for the CourseCertificate model."""
    list_display = ('course_id', 'certificate_type', 'site', 'is_active')
    list_filter = ('certificate_type', 'is_active')
    search_fields = ('course_id',)


class ProgramCertificateAdmin(admin.ModelAdmin):
    """Admin for the ProgramCertificate model."""
    form = ProgramCertificateAdminForm
    list_display = ('program_uuid', 'site', 'is_active')
    list_filter = ('is_active', 'site',)
    search_fields = ('program_id', 'program_uuid',)


class SignatoryAdmin(admin.ModelAdmin):
    """Admin for the Signatory model."""
    form = SignatoryModelForm
    list_display = ('name', 'title', 'image')
    search_fields = ('name',)


admin.site.register(CertificateTemplateAsset, CertificateTemplateAssetAdmin)
admin.site.register(CertificateTemplate, CertificateTemplateAdmin)
admin.site.register(CourseCertificate, CourseCertificateAdmin)
admin.site.register(ProgramCertificate, ProgramCertificateAdmin)
admin.site.register(Signatory, SignatoryAdmin)
admin.site.register(UserCredential, UserCredentialAdmin)
