"""
Admin section configuration.
"""

from django.contrib import admin, messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from credentials.apps.badges.admin_forms import (
    BadgePenaltyForm,
    BadgeRequirementForm,
    BadgeRequirementFormSet,
    CredlyOrganizationAdminForm,
    DataRuleForm,
    DataRuleFormSet,
    PenaltyDataRuleForm,
    PenaltyDataRuleFormSet,
)
from credentials.apps.badges.exceptions import BadgeProviderError
from credentials.apps.badges.models import (
    AccredibleAPIConfig,
    AccredibleBadge,
    AccredibleGroup,
    BadgePenalty,
    BadgeProgress,
    BadgeRequirement,
    CredlyBadge,
    CredlyBadgeTemplate,
    CredlyOrganization,
    DataRule,
    Fulfillment,
    PenaltyDataRule,
)
from credentials.apps.badges.toggles import is_badges_enabled


ADMIN_CHANGE_VIEW_REVERSE_NAMES = {
    CredlyBadgeTemplate.ORIGIN: "admin:badges_credlybadgetemplate_change",
    AccredibleGroup.ORIGIN: "admin:badges_accrediblegroup_change",
}


class BadgeRequirementInline(admin.TabularInline):
    """
    Badge template requirement inline setup.
    """

    model = BadgeRequirement
    show_change_link = True
    extra = 0
    fields = (
        "event_type",
        "rules",
        "description",
        "blend",
    )
    readonly_fields = ("rules",)
    ordering = ("blend",)
    form = BadgeRequirementForm
    formset = BadgeRequirementFormSet

    def rules(self, obj):
        """
        Display all data rules for the requirement.
        """
        return (
            format_html(
                "<ul>{}</ul>",
                mark_safe(
                    "".join(
                        f"<li>{rule.data_path} {rule.OPERATORS[rule.operator]} {rule.value}</li>"
                        for rule in obj.rules.all()
                    )
                ),
            )
            if obj.rules.exists()
            else _("No rules specified.")
        )


class BadgePenaltyInline(admin.TabularInline):
    """
    Badge template penalty inline setup.
    """

    model = BadgePenalty
    show_change_link = True
    extra = 0
    fields = (
        "event_type",
        "rules",
        "requirements",
    )
    readonly_fields = ("rules",)
    form = BadgePenaltyForm

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Filter requirements by parent badge template.
        """
        if db_field.name == "requirements":
            template_id = request.resolver_match.kwargs.get("object_id")
            if template_id:
                kwargs["queryset"] = BadgeRequirement.objects.filter(template_id=template_id)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def rules(self, obj):
        """
        Display all data rules for the penalty.
        """
        return (
            format_html(
                "<ul>{}</ul>",
                mark_safe(
                    "".join(
                        f"<li>{rule.data_path} {rule.OPERATORS[rule.operator]} {rule.value}</li>"
                        for rule in obj.rules.all()
                    )
                ),
            )
            if obj.rules.exists()
            else _("No rules specified.")
        )


class FulfillmentInline(admin.TabularInline):
    """
    Badge template fulfillment inline setup.
    """

    model = Fulfillment
    extra = 0
    readonly_fields = [
        "requirement",
    ]


class DataRuleInline(admin.TabularInline):
    """
    Data rule inline setup.
    """

    model = DataRule
    extra = 0
    form = DataRuleForm
    formset = DataRuleFormSet


class CredlyOrganizationAdmin(admin.ModelAdmin):
    """
    Credly organization admin setup.
    """

    form = CredlyOrganizationAdminForm
    list_display = (
        "name",
        "uuid",
        "api_key_hidden",
    )
    fields = [
        "name",
        "uuid",
        "api_key_hidden",
    ]
    readonly_fields = [
        "name",
    ]
    actions = ("sync_organization_badge_templates",)

    @admin.action(description="Sync organization badge templates")
    def sync_organization_badge_templates(self, request, queryset):
        """
        Sync badge templates for selected organizations.
        """
        site = get_current_site(request)
        for organization in queryset:
            call_command(
                "sync_organization_badge_templates",
                organization_id=organization.uuid,
                site_id=site.id,
            )

        messages.success(request, _("Badge templates were successfully updated."))

    @admin.display(description=_("API key"))
    def api_key_hidden(self, obj):
        """
        Hide API key and display text.
        """

        return _("Pre-configured from the environment.") if obj.is_preconfigured else obj.api_key

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        if not (obj and obj.is_preconfigured):
            fields = [field for field in fields if field != "api_key_hidden"]
            fields.append("api_key")
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))

        if not obj:
            return readonly_fields

        if obj.is_preconfigured:
            readonly_fields.append("api_key_hidden")
        return readonly_fields


class CredlyBadgeTemplateAdmin(admin.ModelAdmin):
    """
    Badge template admin setup.
    """

    exclude = [
        "icon",
    ]
    list_display = (
        "organization",
        "state",
        "name",
        "uuid",
        "is_active",
        "image",
    )
    list_filter = (
        "organization",
        "is_active",
        "state",
    )
    search_fields = (
        "name",
        "uuid",
    )
    readonly_fields = [
        "organization",
        "origin",
        "state",
        "dashboard_link",
        "image",
    ]
    fieldsets = (
        (
            "Generic",
            {
                "fields": (
                    "site",
                    "is_active",
                ),
                "description": _(
                    """
                    WARNING: avoid configuration updates on activated badges.
                    Active badge templates are continuously processed and learners may already have progress on them.
                    Any changes in badge template requirements (including data rules) will affect learners' experience!
                    """
                ),
            },
        ),
        (
            "Badge template",
            {
                "fields": (
                    "uuid",
                    "name",
                    "description",
                    "image",
                    "origin",
                )
            },
        ),
        (
            "Credly",
            {
                "fields": (
                    "organization",
                    "state",
                    "dashboard_link",
                ),
            },
        ),
    )
    inlines = [
        BadgeRequirementInline,
        BadgePenaltyInline,
    ]

    def has_add_permission(self, request):
        return False

    def dashboard_link(self, obj):
        url = obj.management_url
        return format_html("<a href='{url}'>{url}</a>", url=url)

    def delete_model(self, request, obj):
        """
        Prevent deletion of active badge templates.
        """
        if obj.is_active:
            messages.set_level(request, messages.ERROR)
            messages.error(request, _("Active badge template cannot be deleted."))
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Prevent deletion of active badge templates.
        """
        if queryset.filter(is_active=True).exists():
            messages.set_level(request, messages.ERROR)
            messages.error(request, _("Active badge templates cannot be deleted."))
            return
        super().delete_queryset(request, queryset)

    def image(self, obj):
        """
        Badge template preview image.
        """
        if obj.icon:
            return format_html('<img src="{}" width="50" height="auto" />', obj.icon)
        return None

    image.short_description = _("icon")

    def save_model(self, request, obj, form, change):
        pass

    def save_formset(self, request, form, formset, change):
        """
        Check if template is active and has requirements.
        """
        formset.save()

        if form.instance.is_active and not form.instance.requirements.exists():
            messages.set_level(request, messages.ERROR)
            messages.error(request, _("Active badge template must have at least one requirement."))
            return HttpResponseRedirect(request.path)
        return form.instance.save()


class DataRulePenaltyInline(admin.TabularInline):
    model = PenaltyDataRule
    extra = 0
    form = PenaltyDataRuleForm
    formset = PenaltyDataRuleFormSet


class BadgeRequirementAdmin(admin.ModelAdmin):
    """
    Badge template requirement admin setup.
    """

    inlines = [
        DataRuleInline,
    ]

    list_display = [
        "id",
        "__str__",
        "event_type",
        "template_link",
    ]
    list_display_links = (
        "id",
        "__str__",
    )
    list_filter = [
        "template",
        "event_type",
    ]
    readonly_fields = [
        "template",
        "event_type",
        "template_link",
        "blend",
    ]

    fields = [
        "template_link",
        "event_type",
        "description",
        "blend",
    ]

    def has_add_permission(self, request):
        return False

    def template_link(self, instance):
        """
        Interactive link to parent (badge template).
        """
        reverse_name = ADMIN_CHANGE_VIEW_REVERSE_NAMES.get(instance.template.origin, "admin:index")
        reverse_args = [] if reverse_name == "admin:index" else [instance.template.pk]

        url = reverse(reverse_name, args=reverse_args)
        return format_html('<a href="{}">{}</a>', url, instance.template)

    template_link.short_description = _("badge template")

    def response_change(self, request, obj):
        if "_save" in request.POST:
            reverse_name = ADMIN_CHANGE_VIEW_REVERSE_NAMES.get(obj.template.origin, "admin:index")
            reverse_args = [] if reverse_name == "admin:index" else [obj.template.pk]
            return HttpResponseRedirect(reverse(reverse_name, args=reverse_args))
        return super().response_change(request, obj)


class BadgePenaltyAdmin(admin.ModelAdmin):
    """
    Badge requirement penalty setup admin.
    """

    inlines = [
        DataRulePenaltyInline,
    ]

    list_display_links = (
        "id",
        "template",
    )
    list_display = [
        "id",
        "__str__",
        "event_type",
        "template_link",
    ]
    list_display_links = (
        "id",
        "__str__",
    )
    list_filter = [
        "template",
        "requirements",
    ]
    fields = [
        "template_link",
        "event_type",
        "requirements",
    ]
    readonly_fields = [
        "template_link",
        "event_type",
        "requirements",
    ]
    form = BadgePenaltyForm

    def has_add_permission(self, request):
        return False

    def template_link(self, instance):
        """
        Interactive link to parent (badge template).
        """
        reverse_name = ADMIN_CHANGE_VIEW_REVERSE_NAMES.get(instance.template.origin, "admin:index")
        reverse_args = [] if reverse_name == "admin:index" else [instance.template.pk]
        url = reverse(reverse_name, args=reverse_args)
        return format_html('<a href="{}">{}</a>', url, instance.template)

    template_link.short_description = _("badge template")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "requirements":
            object_id = request.resolver_match.kwargs.get("object_id")
            template_id = self.get_object(request, object_id).template_id
            if template_id:
                kwargs["queryset"] = BadgeRequirement.objects.filter(template_id=template_id)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def response_change(self, request, obj):
        if "_save" in request.POST:
            reverse_name = ADMIN_CHANGE_VIEW_REVERSE_NAMES.get(obj.template.origin, "admin:index")
            reverse_args = [] if reverse_name == "admin:index" else [obj.template.pk]
            return HttpResponseRedirect(reverse(reverse_name, args=reverse_args))
        return super().response_change(request, obj)


class BadgeProgressAdmin(admin.ModelAdmin):
    """
    Badge template progress admin setup.
    """

    inlines = [
        FulfillmentInline,
    ]
    list_display = [
        "id",
        "username",
        "template",
        "complete",
    ]
    list_display_links = (
        "id",
        "username",
        "template",
    )
    readonly_fields = (
        "username",
        "template",
        "complete",
        "ratio",
    )

    @admin.display(boolean=True)
    def complete(self, obj):
        """
        Identifies if all requirements are already fulfilled.

        NOTE: (performance) dynamic evaluation.
        """
        return obj.completed

    def ratio(self, obj):
        """
        Displays progress value.
        """
        return obj.ratio

    def has_add_permission(self, request):
        return False


class CredlyBadgeAdmin(admin.ModelAdmin):
    """
    Credly badge admin setup.
    """

    list_display = (
        "uuid",
        "username",
        "credential",
        "status",
        "state",
        "external_uuid",
    )
    list_filter = (
        "status",
        "state",
    )
    search_fields = (
        "username",
        "external_uuid",
    )
    readonly_fields = (
        "credential_id",
        "credential_content_type",
        "username",
        "state",
        "uuid",
        "external_uuid",
    )

    def has_add_permission(self, request):
        return False


class AccredibleAPIConfigAdmin(admin.ModelAdmin):
    """
    Accredible API configuration admin setup.
    """

    list_display = (
        "id",
        "name",
    )
    actions = ("sync_groups",)

    @admin.action(description="Sync groups")
    def sync_groups(self, request, queryset):
        """
        Sync groups for selected api configs.
        """
        site = get_current_site(request)
        for api_config in queryset:
            try:
                call_command(
                    "sync_accredible_groups",
                    api_config_id=api_config.id,
                    site_id=site.id,
                )
            except BadgeProviderError as exc:
                messages.set_level(request, messages.ERROR)
                messages.error(request, _("Failed to sync groups for API config: {}. {}").format(api_config.name, exc))

        messages.success(request, _("Accredible groups were successfully updated."))


class AccredibleBadgeAdmin(admin.ModelAdmin):
    """
    Accredible badge admin setup.
    """

    list_display = (
        "uuid",
        "username",
        "credential",
        "status",
        "state",
        "external_id",
    )
    list_filter = (
        "status",
        "state",
    )
    search_fields = (
        "username",
        "external_id",
    )
    readonly_fields = (
        "credential_id",
        "credential_content_type",
        "username",
        "state",
        "uuid",
        "external_id",
    )

    def has_add_permission(self, request):
        return False


class AccredibleGroupAdmin(admin.ModelAdmin):
    """
    Accredible group admin setup.
    """

    list_display = (
        "id",
        "api_config",
        "name",
        "state",
        "is_active",
        "image",
    )
    list_filter = (
        "api_config",
        "is_active",
        "state",
    )
    search_fields = (
        "name",
        "id",
    )
    readonly_fields = [
        "state",
        "origin",
        "dashboard_link",
        "image",
    ]
    fieldsets = (
        (
            "Generic",
            {
                "fields": (
                    "site",
                    "is_active",
                ),
                "description": _(
                    """
                    WARNING: avoid configuration updates on activated badges.
                    Active badge templates are continuously processed and learners may already have progress on them.
                    Any changes in badge template requirements (including data rules) will affect learners' experience!
                    """
                ),
            },
        ),
        (
            "Badge template",
            {
                "fields": (
                    "name",
                    "description",
                    "image",
                    "origin",
                )
            },
        ),
        (
            "Accredible",
            {
                "fields": (
                    "api_config",
                    "state",
                    "dashboard_link",
                ),
            },
        ),
    )
    inlines = [
        BadgeRequirementInline,
        BadgePenaltyInline,
    ]

    def has_add_permission(self, request):
        return False

    def dashboard_link(self, obj):
        url = obj.management_url
        return format_html("<a href='{url}'>{url}</a>", url=url)

    def delete_model(self, request, obj):
        """
        Prevent deletion of active badge templates.
        """
        if obj.is_active:
            messages.set_level(request, messages.ERROR)
            messages.error(request, _("Active badge template cannot be deleted."))
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Prevent deletion of active badge templates.
        """
        if queryset.filter(is_active=True).exists():
            messages.set_level(request, messages.ERROR)
            messages.error(request, _("Active badge templates cannot be deleted."))
            return
        super().delete_queryset(request, queryset)

    def image(self, obj):
        """
        Badge template preview image.
        """
        if obj.icon:
            return format_html('<img src="{}" width="50" height="auto" />', obj.icon)
        return None


# register admin configurations with respect to the feature flag
if is_badges_enabled():
    admin.site.register(CredlyOrganization, CredlyOrganizationAdmin)
    admin.site.register(CredlyBadgeTemplate, CredlyBadgeTemplateAdmin)
    admin.site.register(CredlyBadge, CredlyBadgeAdmin)
    admin.site.register(BadgeRequirement, BadgeRequirementAdmin)
    admin.site.register(BadgePenalty, BadgePenaltyAdmin)
    admin.site.register(BadgeProgress, BadgeProgressAdmin)
    admin.site.register(AccredibleAPIConfig, AccredibleAPIConfigAdmin)
    admin.site.register(AccredibleBadge, AccredibleBadgeAdmin)
    admin.site.register(AccredibleGroup, AccredibleGroupAdmin)
