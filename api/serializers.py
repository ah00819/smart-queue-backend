from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from django.db import transaction
from .validators import ExactLengthValidator
from appointment.models import (
    Appointment,
    AppointmentRequest,
    Service,
    StaffMember,
    Config,
    PaymentInfo,
    DayOff,
    WorkingHours,
)
from .models import Organization, Address, Branch, ServiceCounter
from django.contrib.auth import get_user_model


User = get_user_model()


class SimpleServiceSerializer(serializers.ModelSerializer):
    price = serializers.CharField(source="get_price_text", read_only=True)

    def get_price(self, service: Service):
        return service.get_price_text()

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "price",
            "image",
        ]


class ServiceSerializer(serializers.ModelSerializer):
    currency = serializers.CharField(
        default="EGP", validators=[ExactLengthValidator(3)], label=_("Currency")
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


class SimpleStaffMemberSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField(method_name="get_fullname")
    email = serializers.EmailField(source="user.email", read_only=True)

    def get_fullname(self, staff_member: StaffMember):
        return f"{staff_member.user.first_name} {staff_member.user.last_name}".strip()

    class Meta:
        model = StaffMember
        fields = ["id", "fullname", "email"]


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "full_name", "email"]


class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = ["id", "day_of_week", "start_time", "end_time"]


class StaffMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    services_offered = serializers.StringRelatedField(many=True)
    working_hours = WorkingHoursSerializer(
        read_only=True, many=True, source="workinghours_set"
    )

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
            # NOTE: sill don't know what that is for?
            "id_request",
        ]


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
            # NOTE: I don't know what id_request is used for.
            "id_request",  # An ID for the appointment.
        ]
        read_only_fields = ["client", "id_request"]


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


class PaymentInfoSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)

    class Meta:
        model = PaymentInfo
        fields = ["id", "appointment"]


class CreatePaymentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentInfo
        fields = ["id", "appointment"]


class DayOffSerializer(serializers.ModelSerializer):
    staff_member = SimpleStaffMemberSerializer(read_only=True)

    class Meta:
        model = DayOff
        fields = ["id", "staff_member", "start_date", "end_date", "description"]


class CreateDayOffSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayOff
        fields = ["staff_member", "start_date", "end_date", "description"]


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


class SimpleAddressSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    def get_address(self, address: Address):
        return f"{address.address}, {address.city}, {address.country}"

    class Meta:
        model = Address
        fields = [
            "id",
            "address",
        ]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "address",
            "city",
            "country",
            "postal_code",
            "latitude",
            "longitude",
        ]


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


class ServiceCounterSerializer(serializers.ModelSerializer):
    branch = BranchSerializer()
    service = SimpleServiceSerializer()
    staff_member = SimpleStaffMemberSerializer()

    class Meta:
        model = ServiceCounter
        fields = ["id", "name", "branch", "service", "staff_member", "is_operational"]


class CreateServiceCounterSerializer(serializers.ModelSerializer):
    is_operational = serializers.BooleanField(
        read_only=True, initial=True, label=_("Is Operational")
    )

    class Meta:
        model = ServiceCounter
        fields = ["id", "name", "branch", "service", "staff_member", "is_operational"]

    def validate(self, data):
        # create or update records
        staff_member = data.get(
            "staff_member", getattr(self.instance, "staff_member", None)
        )
        service = data.get("service", getattr(self.instance, "service", None))
        if staff_member and service:
            if service not in staff_member.services_offered.all():
                # validate if staff_member can offer the assigned service or not
                raise serializers.ValidationError(
                    {
                        "staff_member": _(
                            "This staff member is not authorized for this service."
                        )
                    }
                )
        return data
