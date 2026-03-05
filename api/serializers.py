from django.db import transaction
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from appointment.models import (
    Appointment,
    AppointmentRequest,
    Service,
    StaffMember,
    Config,
    DayOff,
    WorkingHours,
)
from .validators import ExactLengthValidator
from .models import STAFF_GROUP, Client, Organization, Address, Branch, ServiceCounter


# Address Serializers
class BaseAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "address", "city", "country"]


class AddressSerializer(BaseAddressSerializer):
    class Meta(BaseAddressSerializer.Meta):
        fields = BaseAddressSerializer.Meta.fields + [
            "postal_code",
            "latitude",
            "longitude",
        ]


class SimpleAddressSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = ["id", "address"]

    def get_address(self, obj):
        return f"{obj.address}, {obj.city}, {obj.country}"


# Client Serializers


class ClientSerializer(serializers.ModelSerializer):
    address = SimpleAddressSerializer()

    class Meta:
        model = Client
        fields = [
            "id",
            "user",
            "phone",
            "address",
            "national_id",
            "birth_date",
            "profession",
            "gender",
            "address",
            "image",
        ]


class CreateClientSerializer(serializers.ModelSerializer):
    address = BaseAddressSerializer(required=False, allow_null=True)

    class Meta:
        model = Client
        fields = [
            "user",  # a user shouldn't be missing with this
            "national_id",
            "birth_date",
            "profession",
            "gender",
            "address",
            "image",
        ]

    def create(self, validated_data):
        address_data = validated_data.pop("address", None)
        address = Address.objects.create(**address_data) if address_data else None
        return Client.objects.create(address=address, **validated_data)


# Service Serializers


class SimpleServiceSerializer(serializers.ModelSerializer):
    price = serializers.CharField(source="get_price_text", read_only=True)

    class Meta:
        model = Service
        fields = ["id", "name", "description", "price", "image"]


class ServiceSerializer(serializers.ModelSerializer):
    currency = serializers.CharField(
        default="EGP",
        validators=[ExactLengthValidator(3)],
        label=_("Currency"),
    )

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "duration",
            "price",
            "down_payment",
            "currency",
            "image",
            "reschedule_limit",
            "allow_rescheduling",
        ]


# Working Hours Serializers


class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = ["id", "day_of_week", "start_time", "end_time"]


# Day off Serializers


class DayOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOff
        fields = ["id", "start_date", "end_date", "description"]


# Staff Member Serializers


class SimpleStaffMemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StaffMember
        fields = ["id", "name", "email"]


class StaffMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    services_offered = serializers.StringRelatedField(many=True)
    working_hours = WorkingHoursSerializer(
        many=True, read_only=True, source="workinghours_set"
    )
    days_off = DayOffSerializer(many=True, read_only=True, source="dayoff_set")

    class Meta:
        model = StaffMember
        fields = [
            "id",
            "user",
            "services_offered",
            "slot_duration",
            "lead_time",
            "finish_time",
            "appointment_buffer_time",
            "work_on_saturday",
            "work_on_sunday",
            "working_hours",
            "days_off",
        ]


class CreateStaffMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMember
        fields = [
            "id",
            "user",
            "services_offered",
            "slot_duration",
            "lead_time",
            "finish_time",
            "appointment_buffer_time",
            "work_on_saturday",
            "work_on_sunday",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            staff_member = super().create(validated_data)
            user = staff_member.user
            staff_group, __ = Group.objects.get_or_create(name=STAFF_GROUP)
            user.groups.add(staff_group)
            user.save()
            return staff_member


# AppointmentRequest Serializers
# NOTE: I've no idea what AppointmentRequest.id_request is for!


class AppointmentRequestSerializer(serializers.ModelSerializer):
    service = SimpleServiceSerializer(read_only=True)
    staff_member = SimpleStaffMemberSerializer(read_only=True)

    class Meta:
        model = AppointmentRequest
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "service",
            "staff_member",
            "payment_type",
            "reschedule_attempts",
            "id_request",
        ]


class CreateAppointmentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentRequest
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "service",
            "staff_member",
            "payment_type",
            "reschedule_attempts",
            "id_request",
        ]


# Appointment Serializers


class AppointmentSerializer(serializers.ModelSerializer):
    # changed the help_text
    address = serializers.CharField(
        max_length=255,
        allow_blank=True,
        label=_("Address"),
        help_text=_("Does not have to be specific, just the city and the country"),
    )
    # chagned initial to True
    want_reminder = serializers.BooleanField(
        initial=True,
        label=_("Want Reminder"),
        help_text=_(
            "Indicates whether the client wants a reminder for the appointment."
        ),
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "client",
            "appointment_request",
            "phone",  # The client's phone number
            "address",
            "want_reminder",
            "additional_info",
            "paid",
            "amount_to_pay",
            "id_request",  # An ID for the appointment.
        ]
        read_only_fields = ["client", "id_request"]


# Config Serializers


class ConfigSerializer(serializers.ModelSerializer):
    """App Global Configurations"""

    class Meta:
        model = Config
        fields = [
            "id",
            "slot_duration",
            "lead_time",
            "finish_time",
            "appointment_buffer_time",
            "website_name",
            "app_offered_by_label",
            "default_reschedule_limit",
            "allow_staff_change_on_reschedule",
        ]


# Organization Serializers


class OrganizationSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "code",
            "brief",
            "image",
            "email",
            "website",
            "is_active",
        ]


# Branch Serializers


class BranchSerializer(serializers.ModelSerializer):
    address = SimpleAddressSerializer()

    class Meta:
        model = Branch
        fields = [
            "id",
            "organization",
            "name",
            "email",
            "phone",
            "address",
            "is_active",
        ]


class CreateBranchSerializer(serializers.ModelSerializer):
    address = AddressSerializer()

    class Meta:
        model = Branch
        fields = [
            "id",
            "organization",
            "name",
            "email",
            "phone",
            "address",
        ]

    def create(self, validated_data):
        address_data = validated_data.pop("address")
        with transaction.atomic():
            address = Address.objects.create(**address_data)
            branch = Branch.objects.create(address=address, **validated_data)
            return branch

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        with transaction.atomic():
            if address_data:
                address_serializer = AddressSerializer(
                    instance.address, data=address_data, partial=True
                )
                address_serializer.is_valid(raise_exception=True)
                address_serializer.save()
            return super().update(instance, validated_data)


# Service Counter Serializer


class ServiceCounterSerializer(serializers.ModelSerializer):
    branch = BranchSerializer()
    service = SimpleServiceSerializer()
    staff_member = SimpleStaffMemberSerializer()

    class Meta:
        model = ServiceCounter
        fields = ["id", "name", "branch", "service", "staff_member", "is_operational"]


class CreateServiceCounterSerializer(serializers.ModelSerializer):
    is_operational = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = ServiceCounter
        fields = ["id", "name", "branch", "service", "staff_member", "is_operational"]

    def validate(self, attrs):
        staff = attrs.get("staff_member", getattr(self.instance, "staff_member", None))
        service = attrs.get("service", getattr(self.instance, "service", None))

        if staff and service and service not in staff.services_offered.all():
            raise serializers.ValidationError(
                {"staff_member": _("Staff member cannot offer this service.")}
            )
        return attrs


# Mixins
class ReadWriteSerializerMixin:
    read_serializer = None
    write_serializer = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return self.write_serializer
        return self.read_serializer
