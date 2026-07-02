from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import *
from api.pagenation import DefaultPagination
from .permissions import (
    IsAdminOrReadOnly,
    AppointmentPermissions,
    IsOwnerOrAdmin,
    IsStaffMemberOrAdminOrReadOnly,
)
from .models import Client, Organization, Branch, ServiceCounter
from .serializers import *
from rest_framework.decorators import action
from datetime import date as date_obj
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.decorators import action

# Create your views here.


class ClientViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = ClientSerializer
    write_serializer = CreateClientSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.select_related("user")
        return queryset if user.is_staff else queryset.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AppointmentViewSet(ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, AppointmentPermissions]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related(
            "client__user",
            "counter__branch",
            "counter__staff_member__user",
            "counter__service",
        )
        if user.is_staff:
            return queryset

        if user.groups.filter(name="Service Staff Member").exists():
            return queryset.filter(counter__staff_member__user=user)

        return queryset.filter(client__user=user)

    def perform_create(self, serializer):
        client = Client.objects.get(user=self.request.user)
        serializer.save(client=client)


class StaffMemberViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = StaffMemberSerializer
    write_serializer = CreateStaffMemberSerializer
    queryset = (
        StaffMember.objects.select_related("user", "organization")
        .prefetch_related("services_offered", "workdays")
        .all()
    )
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]
    pagination_class = DefaultPagination


class WorkDayViewSet(ModelViewSet):
    serializer_class = WorkDaySerializer
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]

    def get_queryset(self):
        staff_member_pk = self.kwargs.get("staff_member_pk")
        branch_pk = self.kwargs.get("branch_pk")

        if staff_member_pk:
            return WorkDay.objects.filter(staff_members__id=staff_member_pk)
        if branch_pk:
            return WorkDay.objects.filter(branches__id=branch_pk)

        return WorkDay.objects.all()

    def perform_create(self, serializer):
        staff_member_pk = self.kwargs.get("staff_member_pk")
        branch_pk = self.kwargs.get("branch_pk")

        workday = serializer.save()

        # Link it to the parent if the PK exists in the URL
        if staff_member_pk:
            staff = get_object_or_404(StaffMember, pk=staff_member_pk)
            staff.workdays.add(workday)
        elif branch_pk:
            branch = get_object_or_404(Branch, pk=branch_pk)
            branch.operating_hours.add(workday)


class LeaveRequestViewSet(ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]

    def get_queryset(self):
        staff_member_pk = self.kwargs.get("staff_member_pk")
        if staff_member_pk:
            return LeaveRequest.objects.filter(staff_member_id=staff_member_pk)
        return LeaveRequest.objects.all()


class ServiceViewSet(ModelViewSet):
    queryset = (
        Service.objects.select_related("organization").prefetch_related(
            "required_documents"
        )
    )
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination


class OrganizationViewSet(ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination


class BranchViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = BranchSerializer
    write_serializer = CreateBranchSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination

    def get_queryset(self):
        org_pk = self.kwargs.get("organization_pk")
        queryset = Branch.objects.select_related("address")
        return queryset.filter(organization_id=org_pk) if org_pk else queryset


class ServiceCounterViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = ServiceCounterSerializer
    write_serializer = CreateServiceCounterSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination

    def get_queryset(self):
        branch_pk = self.kwargs.get("branch_pk")
        queryset = ServiceCounter.objects.select_related(
            "staff_member__user", "service", "branch"
        )
        return queryset.filter(branch_id=branch_pk) if branch_pk else queryset

    @action(detail=True, methods=["get"])
    def available_slots(self, request, pk=None, organization_pk=None, branch_pk=None):
        counter = self.get_object()
        date_str = request.query_params.get("date")
        today = timezone.now().date()
        if date_str:
            try:
                # parse date query filters: ?date=2026-04-08
                selected_date = date_obj.fromisoformat(date_str)
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"}, status=400
                )

            if selected_date < today:
                return Response(
                    {"error": "Cannot retrieve slots for a past date."}, status=400
                )
        else:
            # If no date provided, use the current date from Django's timezone util
            selected_date = timezone.now().date()

        slots = counter.get_available_slots(selected_date)

        return Response({"date": selected_date.isoformat(), "slots": slots})


class RequiredDocumentViewSet(ModelViewSet):
    serializer_class = RequiredDocumentSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        service_pk = self.kwargs.get("service_pk")
        if service_pk:
            return RequiredDocument.objects.filter(service_id=service_pk)
        return RequiredDocument.objects.all()

    def perform_create(self, serializer):
        service_pk = self.kwargs.get("service_pk")
        serializer.save(service_id=service_pk)


class AttachedDocumentViewSet(ModelViewSet):
    serializer_class = AttachedDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        appointment_pk = self.kwargs.get("appointment_pk")
        user = self.request.user
        queryset = AttachedDocument.objects.filter(appointment_id=appointment_pk)

        if not user.is_staff:
            queryset = queryset.filter(appointment__client__user=user)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["appointment_pk"] = self.kwargs.get("appointment_pk")
        return context

    def perform_create(self, serializer):
        appointment_pk = self.kwargs.get("appointment_pk")
        serializer.save(appointment_id=appointment_pk)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)

        fields = getattr(serializer, "fields", None)
        if fields is None and hasattr(serializer, "child"):
            fields = serializer.child.fields

        if fields and "document" in fields:
            appointment_pk = self.kwargs.get("appointment_pk")
            try:
                appointment = Appointment.objects.select_related(
                    "counter__service"
                ).get(pk=appointment_pk)
                fields["document"].queryset = RequiredDocument.objects.filter(
                    service=appointment.counter.service
                )
            except Appointment.DoesNotExist:
                fields["document"].queryset = RequiredDocument.objects.none()

        return serializer


from django.shortcuts import get_object_or_404


class ServiceFeedbackViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = ServiceFeedbackSerializer
    write_serializer = CreateServiceFeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        appointment_pk = self.kwargs.get("appointment_pk")
        return ServiceFeedback.objects.filter(appointment_id=appointment_pk)

    def perform_create(self, serializer):
        appointment_pk = self.kwargs.get("appointment_pk")

        appointment = get_object_or_404(Appointment, pk=appointment_pk)
        client = get_object_or_404(Client, user=self.request.user)

        if appointment.client != client:
            raise serializer.PermissionDenied(
                "You can only provide feedback for your own appointments."
            )
        if ServiceFeedback.objects.filter(
            client=client, appointment=appointment
        ).exists():
            raise serializer.ValidationError(
                "You have already provided feedback for this appointment."
            )
        serializer.save(client=client, appointment=appointment)


from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        client_id = self.request.query_params.get("client_id")

        return Notification.objects.filter(client_id=client_id).order_by("-created_at")
