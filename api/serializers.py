import datetime
from datetime import datetime
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import *


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
    class Meta:
        model = Service
        fields = ["id", "name", "description", "price", "duration", "currency", "image"]


from django.db import transaction


class RequiredDocumentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Important for updates

    class Meta:
        model = RequiredDocument
        fields = ["id", "name", "description", "is_mandatory"]


class ServiceSerializer(serializers.ModelSerializer):
    required_documents = RequiredDocumentSerializer(many=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "description",
            "organization",
            "duration",
            "price",
            "currency",
            "image",
            "reschedule_limit",
            "required_documents",
        ]

    def create(self, validated_data):
        docs_data = validated_data.pop("required_documents", [])

        with transaction.atomic():
            service = Service.objects.create(**validated_data)
            for doc in docs_data:
                RequiredDocument.objects.create(service=service, **doc)
            return service

    def update(self, instance, validated_data):
        docs_data = validated_data.pop("required_documents", None)

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if docs_data is not None:
                instance.required_documents.all().delete()
                for doc in docs_data:
                    doc.pop("id", None)
                    RequiredDocument.objects.create(service=instance, **doc)

            return instance


# Organization Serializers
class OrganizationSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, read_only=True)
    services = SimpleServiceSerializer(many=True, read_only=True)

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
            "services",
            "is_active",
        ]


# Work Day Serializers


class WorkDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkDay
        fields = ["id", "weekday", "from_hour", "to_hour"]


# Leave Request (Days Off) Serializers


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ["id", "date", "description", "is_full_day"]


# Staff Member Serializers


class SimpleStaffMemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StaffMember
        fields = ["id", "name", "email"]


class StaffMemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    name = serializers.CharField(source="user.get_full_name", read_only=True)
    services_offered = serializers.StringRelatedField(many=True)
    workdays = WorkDaySerializer(many=True, read_only=True)

    class Meta:
        model = StaffMember
        fields = [
            "id",
            "user",
            "name",
            "organization",
            "services_offered",
            "workdays",
            "phone",
            "national_id",
            "gender",
            "image",
        ]


class CreateStaffMemberSerializer(serializers.ModelSerializer):
    workdays = WorkDaySerializer(many=True, required=False)

    class Meta:
        model = StaffMember
        fields = [
            "user",
            "organization",
            "services_offered",
            "national_id",
            "workdays",
            "phone",
            "gender",
        ]

    def validate(self, attrs):
        org = attrs.get("organization")
        services = attrs.get("services_offered", [])
        for s in services:
            if s.organization != org:
                raise serializers.ValidationError(
                    "Staff cannot offer services from another organization."
                )
        return attrs

    def create(self, validated_data):
        services = validated_data.pop("services_offered", [])
        workdays_data = validated_data.pop("workdays", [])

        with transaction.atomic():
            staff_member = StaffMember.objects.create(**validated_data)
            staff_member.services_offered.set(services)

            # Create or find the workdays and link them
            for day_data in workdays_data:
                day_obj, _ = WorkDay.objects.get_or_create(**day_data)
                staff_member.workdays.add(day_obj)

            # Add to Staff Group
            staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP)
            staff_member.user.groups.add(staff_group)
            return staff_member


# Holiday Serializers
class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ["id", "name", "date"]


# Branch Serializers


class BranchSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    services = SimpleServiceSerializer(many=True, read_only=True)
    operating_hours = WorkDaySerializer(many=True, read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id",
            "organization",
            "name",
            "address",
            "email",
            "phone",
            "services",
            "operating_hours",
            "is_active",
        ]


class CreateBranchSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    operating_hours = WorkDaySerializer(many=True, required=False)
    services = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Service.objects.all(), required=False
    )

    class Meta:
        model = Branch
        fields = [
            "id",
            "organization",
            "name",
            "email",
            "phone",
            "address",
            "services",
            "operating_hours",
        ]

    def validate(self, attrs):
        organization = attrs.get("organization")
        services = attrs.get("services", [])
        # check branch services is subset of its parent organization's
        for service in services:
            if service.organization != organization:
                raise serializers.ValidationError(
                    {
                        "services": f"Service '{service.name}' does not belong to organization '{organization.name}'."
                    }
                )
        return attrs

    def create(self, validated_data):
        services = validated_data.pop("services", [])
        hours_data = validated_data.pop("operating_hours", [])
        address_data = validated_data.pop("address")

        with transaction.atomic():
            address = Address.objects.create(**address_data)
            branch = Branch.objects.create(address=address, **validated_data)
            branch.services.set(services)

            for hour in hours_data:
                hour_obj, _ = WorkDay.objects.get_or_create(**hour)
                branch.operating_hours.add(hour_obj)

            return branch

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        hours_data = validated_data.pop("operating_hours", None)
        with transaction.atomic():
            if address_data:
                address_serializer = AddressSerializer(
                    instance.address, data=address_data, partial=True
                )
                address_serializer.is_valid(raise_exception=True)
                address_serializer.save()

            instance = super().update(instance, validated_data)
            if hours_data is not None:
                new_hours = []
                for hour in hours_data:
                    hour_obj, _ = WorkDay.objects.get_or_create(**hour)
                    new_hours.append(hour_obj)
                instance.operating_hours.set(new_hours)

            return instance


# Service Counter Serializer


class ServiceCounterSerializer(serializers.ModelSerializer):
    # branch = BranchSerializer()
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


# Attached Document Serializers


class AttachedDocumentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = AttachedDocument
        fields = [
            "id",
            "document",
            "file",
            "status",
            "rejection_reason",
            "uploaded_at",
        ]
        read_only_fields = ["status", "rejection_reason", "uploaded_at"]

    def validate(self, attrs):
        appointment_pk = self.context["view"].kwargs.get("appointment_pk")
        document_requirement = attrs.get("document")

        if appointment_pk and document_requirement:
            try:
                appointment = Appointment.objects.get(pk=appointment_pk)
                if document_requirement.service != appointment.counter.service:
                    raise serializers.ValidationError(
                        _(
                            "This document is not a requirement for the selected service."
                        )
                    )
            except Appointment.DoesNotExist:
                raise serializers.ValidationError(_("Invalid appointment."))

        return attrs


# Appointment Serializers


class AppointmentSerializer(serializers.ModelSerializer):
    # changed the help_text
    # address = serializers.CharField(
    #     max_length=255,
    #     allow_blank=True,
    #     label=_("Address"),
    #     help_text=_("Does not have to be specific, just the city and the country"),
    # )
    # chagned initial to True
    want_reminder = serializers.BooleanField(
        initial=True,
        label=_("Want Reminder"),
        help_text=_(
            "Indicates whether the client wants a reminder for the appointment."
        ),
    )
    counter_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCounter.objects.all(), source="counter", write_only=True
    )
    counter = ServiceCounterSerializer(read_only=True)
    attached_documents = AttachedDocumentSerializer(many=True, required=False)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "client",
            "counter",  # Output
            "counter_id",  # Input
            "date",
            "start_time",
            "end_time",
            "want_reminder",
            "additional_info",
            "reschedule_attempts",
            "paid",
            "amount_to_pay",
            "attached_documents",
            "canceled",
            "missed",  # admin/staff member only
        ]
        read_only_fields = ["client", "end_time", "reschedule_attempts"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")

        # If user is NOT staff, they cannot change 'missed', 'paid', or 'amount_to_pay'
        if request and not request.user.is_staff:
            fields["missed"].read_only = True
            fields["paid"].read_only = True
            fields["amount_to_pay"].read_only = True

        return fields

    def create(self, validated_data):
        docs_data = validated_data.pop("attached_documents", [])

        with transaction.atomic():
            appointment = Appointment.objects.create(**validated_data)
            for doc in docs_data:
                AttachedDocument.objects.create(appointment=appointment, **doc)
            return appointment

    def update(self, instance, validated_data):
        docs_data = validated_data.pop("attached_documents", None)

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if docs_data is not None:
                existing_ids = [d.id for d in instance.attached_documents.all()]
                for doc in docs_data:
                    doc_id = doc.pop("id", None)
                    if doc_id and doc_id in existing_ids:
                        AttachedDocument.objects.filter(id=doc_id).update(**doc)
                    else:
                        AttachedDocument.objects.create(appointment=instance, **doc)
            return instance

    def validate(self, attrs):
        counter = attrs.get("counter") or (
            self.instance.counter if self.instance else None
        )
        date = attrs.get("date") or (self.instance.date if self.instance else None)
        start_time = attrs.get("start_time") or (
            self.instance.start_time if self.instance else None
        )

        if not counter or not date or not start_time:
            raise serializers.ValidationError(
                _("Counter, date, and start time are required.")
            )

        request = self.context.get("request")
        is_staff = request and request.user.is_authenticated and request.user.is_staff

        if is_staff:
            duration = counter.service.duration
            start_datetime = datetime.combine(date, start_time)
            attrs["end_time"] = (start_datetime + duration).time()
            return attrs

        is_canceling = attrs.get("canceled", False) is True

        is_schedule_unchanged = (
            self.instance
            and attrs.get("counter") is None
            and attrs.get("date") is None
            and attrs.get("start_time") is None
        )

        if is_canceling or is_schedule_unchanged:
            duration = counter.service.duration
            start_datetime = datetime.combine(date, start_time)
            attrs["end_time"] = (start_datetime + duration).time()
            return attrs

        if request and request.user.is_authenticated:
            try:
                client_profile = request.user.client
            except Client.DoesNotExist:
                raise serializers.ValidationError(
                    _("User does not have a client profile.")
                )
        else:
            client_profile = None

        existing_client_appointment = Appointment.objects.filter(
            client=client_profile,
            counter=counter,
            date__gte=datetime.now().date(),
            canceled=False,
        ).exclude(pk=self.instance.pk if self.instance else None)

        if existing_client_appointment.exists():
            raise serializers.ValidationError(
                _("You already have a pending appointment for this counter.")
            )

        if not counter.service or not counter.is_operational:
            raise serializers.ValidationError(
                _("This counter is currently unavailable.")
            )

        duration = counter.service.duration
        start_datetime = datetime.combine(date, start_time)
        calculated_end_time = (start_datetime + duration).time()
        attrs["end_time"] = calculated_end_time

        available_slots = counter.get_available_slots(date)
        requested_start_str = start_time.strftime("%H:%M")
        is_valid_slot = any(
            slot["start"] == requested_start_str for slot in available_slots
        )

        if not is_valid_slot:
            raise serializers.ValidationError(
                _(
                    "The selected time slot is not available for this service on this date."
                )
            )

        overlapping = (
            Appointment.objects.filter(counter=counter, date=date)
            .filter(Q(start_time__lt=calculated_end_time, end_time__gt=start_time))
            .exclude(pk=self.instance.pk if self.instance else None)
        )

        if overlapping.exists():
            raise serializers.ValidationError(_("This slot was just booked."))

        return attrs


# Service Feedback Serializers


class ServiceFeedbackSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)

    class Meta:
        model = ServiceFeedback
        fields = ["client", "appointment", "feedback"]


class CreateServiceFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFeedback
        fields = ["id", "feedback"]


# Required Document Serializers


class SimpleRequiredDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequiredDocument
        fields = ["service", "name", "description", "is_mandatory"]


class RequiredDocumentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = RequiredDocument
        fields = ["id", "name", "description", "is_mandatory"]


# Mixins
class ReadWriteSerializerMixin:
    read_serializer = None
    write_serializer = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return self.write_serializer
        return self.read_serializer
