"""
Django admin page for credential
"""
from django.contrib import admin

from credentials.apps.credentials.models import (
    CertificateTemplate, CourseCertificate, CertificateTemplateAsset,
    ProgramCertificate, Signatory, UserCredentialAttribute, SiteConfiguration,
    UserCredential
)


class UserCredentialAttributeInline(admin.TabularInline):
    """Tabular inline for the UserCredentialAttribute model."""
    model = UserCredentialAttribute
    extra = 1


class UserCredentialAdmin(admin.ModelAdmin):
    """Admin for the UserCredential model."""
    list_display = ('username', 'status', 'credential_content_type')
    list_filter = ('status', 'credential_content_type')
    search_fields = ('username',)
    inlines = (UserCredentialAttributeInline,)


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
    list_display = ('program_id', 'site', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('program_id',)


class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin for the SiteConfiguration model."""
    list_display = ('site', 'lms_url_root')
    search_fields = ('site__name',)


class SignatoryAdmin(admin.ModelAdmin):
    """Admin for the Signatory model."""
    list_display = ('name', 'title', 'image')
    search_fields = ('name',)


admin.site.register(SiteConfiguration, SiteConfigurationAdmin)
admin.site.register(CertificateTemplateAsset, CertificateTemplateAssetAdmin)
admin.site.register(CertificateTemplate, CertificateTemplateAdmin)
admin.site.register(CourseCertificate, CourseCertificateAdmin)
admin.site.register(ProgramCertificate, ProgramCertificateAdmin)
admin.site.register(Signatory, SignatoryAdmin)
admin.site.register(UserCredential, UserCredentialAdmin)
