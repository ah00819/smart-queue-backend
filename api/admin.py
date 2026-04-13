from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from . import models


class WorkDayInline(admin.TabularInline):
    model = models.WorkDay
    extra = 1


class AttachedDocumentInline(admin.TabularInline):
    model = models.AttachedDocument
    extra = 0
    readonly_fields = ["uploaded_at"]


class RequiredDocumentInline(admin.StackedInline):
    model = models.RequiredDocument
    extra = 1


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


@admin.register(models.Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "organization",
        "duration",
        "price_display",
        "reschedule_limit",
    ]
    list_filter = ["organization", "created_at"]
    search_fields = ["name", "description"]
    inlines = [RequiredDocumentInline]

    @admin.display(description=_("Price"))
    def price_display(self, obj):
        return obj.get_price_text()


@admin.register(models.StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ["get_full_name", "organization", "phone", "gender"]
    list_filter = ["organization", "gender"]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "national_id",
    ]
    autocomplete_fields = ["user", "organization"]
    inlines = [WorkDayInline]

    @admin.display(description=_("Full Name"))
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["get_full_name", "phone", "city_display", "is_authenticated"]
    list_filter = ["is_authenticated", "gender"]
    search_fields = ["user__first_name", "user__last_name", "national_id", "phone"]

    @admin.display(description=_("Full Name"))
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    @admin.display(description=_("City"))
    def city_display(self, obj):
        return obj.address.city if obj.address else "-"


@admin.register(models.Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "client_link",
        "date",
        "timeslot",
        "counter",
        "paid",
        "status_tag",
    ]
    list_filter = ["paid", "date", "counter__branch"]
    search_fields = ["client__user__first_name", "client__user__last_name", "id"]
    date_hierarchy = "date"
    inlines = [AttachedDocumentInline]
    readonly_fields = ["created_at", "updated_at"]

    @admin.display(description=_("Time Slot"))
    def timeslot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"

    @admin.display(description=_("Client"))
    def client_link(self, obj):
        if obj.client:
            url = reverse("admin:api_client_change", args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client)
        return "-"

    @admin.display(description=_("Status"))
    def status_tag(self, obj):
        color = "green" if obj.paid else "orange"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            "PAID" if obj.paid else "PENDING",
        )


@admin.register(models.Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["address", "city", "country", "postal_code"]
    search_fields = ["address", "city"]


@admin.register(models.LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ["staff_member", "date", "is_full_day", "description"]
    list_filter = ["date", "is_full_day", "staff_member"]
    search_fields = ["staff_member__user__first_name", "description"]


@admin.register(models.Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ["name", "date"]
    list_sortable = ["date"]


@admin.register(models.ServiceFeedback)
class ServiceFeedbackAdmin(admin.ModelAdmin):
    list_display = ["client", "appointment", "short_feedback"]
    readonly_fields = ["client", "appointment"]

    def short_feedback(self, obj):
        return obj.feedback[:50] + "..." if len(obj.feedback) > 50 else obj.feedback
