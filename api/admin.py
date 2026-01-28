from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from . import models


# Register your models here.


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    fieldsets = (
        (_("Basic Info"), {"fields": ("name", "code", "is_active")}),
        (_("Contact Details"), {"fields": ("email", "website", "image", "thumbnail")}),
    )

    list_display = ["name", "code", "email", "website", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]
    list_per_page = 20
    readonly_fields = ["thumbnail"]

    @admin.display(description=_("Preview"))
    def thumbnail(self, instance):
        if instance.image:
            return format_html(
                '<img src="{}" style="width: 200px; height: 100px;'
                ' object-fit: cover; border-radius: 4px;" />',
                instance.image.url,
            )
        return _("No Image")


@admin.register(models.Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "link_organization", "city_display", "is_active"]
    list_select_related = ["organization", "address"]
    list_filter = [("organization", admin.RelatedOnlyFieldListFilter), "is_active"]
    autocomplete_fields = ["organization"]
    search_fields = ["name", "organization__name", "email"]
    list_per_page = 20
    ordering = ["organization__name", "name"]

    @admin.display(ordering="organization__name", description=_("Organization"))
    def link_organization(self, obj):
        url = reverse("admin:api_organization_change", args=[obj.organization.id])
        return format_html('<a href="{}">{}</a>', url, obj.organization.name)

    @admin.display(description=_("City"))
    def city_display(self, obj):
        return obj.address.city if obj.address else "-"


@admin.register(models.ServiceCounter)
class ServiceCounterAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "link_branch",
        "link_organization",
        "link_service",
        "staff_member",
        "is_operational",
    ]
    list_select_related = [
        "branch",
        "branch__organization",
        "staff_member",
        "staff_member__user",
        "service",
    ]
    list_filter = ["is_operational", "branch__organization", "service"]
    search_fields = ["name", "branch__name", "staff_member__user__first_name"]
    list_per_page = 20

    @admin.display(ordering="branch__organization__name", description=_("Organization"))
    def link_organization(self, obj):
        url = reverse(
            "admin:api_organization_change", args=[obj.branch.organization.id]
        )
        return format_html('<a href="{}">{}</a>', url, obj.branch.organization.name)

    @admin.display(ordering="branch__name", description=_("Branch"))
    def link_branch(self, obj):

        url = reverse("admin:api_branch_change", args=[obj.branch.id])
        return format_html('<a href="{}">{}</a>', url, obj.branch.name)

    @admin.display(ordering="service__name", description=_("Service"))
    def link_service(self, obj):
        url = reverse("admin:appointment_service_change", args=[obj.service.id])
        return format_html('<a href="{}">{}</a>', url, obj.service.name)
