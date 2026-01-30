from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from appointment.models import (
    Appointment,
    AppointmentRequest,
    Config,
    DayOff,
    PaymentInfo,
    StaffMember,
    WorkingHours,
    Service,
)
from .permissions import (
    AppointmentRequestPermissions,
    IsAdminOrReadOnly,
    AppointmentPermissions,
    IsOwnerOrAdmin,
    IsStaffMemberOrAdminOrReadOnly,
)
from .models import Client, Organization, Branch, ServiceCounter
from .serializers import (
    AppointmentRequestSerializer,
    ClientSerializer,
    CreateAppointmentRequestSerializer,
    AppointmentSerializer,
    ConfigSerializer,
    CreateBranchSerializer,
    CreateClientSerializer,
    CreateDayOffSerializer,
    CreatePaymentInfoSerializer,
    CreateServiceCounterSerializer,
    CreateStaffMemberSerializer,
    DayOffSerializer,
    PaymentInfoSerializer,
    StaffMemberSerializer,
    WorkingHoursSerializer,
    ServiceSerializer,
    OrganizationSerializer,
    BranchSerializer,
    ServiceCounterSerializer,
)

# Create your views here.


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["POST", "PATCH", "PUT"]:
            return CreateClientSerializer
        return ClientSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.select_related("user")
        if user.is_staff:
            return queryset.all()

        return queryset.filter(user=user)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, AppointmentPermissions]

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related("appointment_request")
        if user.is_staff:
            return queryset.all()

        if user.groups.filter(name="Service Staff Member").exists():
            return queryset.filter(appointment_request__staff_member__user=user)

        return queryset.filter(client=user)


class AppointmentRequestViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, AppointmentRequestPermissions]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateAppointmentRequestSerializer
        return AppointmentRequestSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = AppointmentRequest.objects.select_related(
            "service", "staff_member", "staff_member__user"
        )

        if user.is_staff:
            return queryset.all()

        if user.groups.filter(name="Service Staff Member").exists():
            return queryset.filter(staff_member__user=user)

        return queryset.filter(appointment__client=user)


class ConfigViewSet(viewsets.ModelViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [IsAdminUser]


class DayOffViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateDayOffSerializer
        return DayOffSerializer

    def get_queryset(self):
        return DayOff.objects.select_related("staff_member", "staff_member__user")


class PaymentInfoViewSet(viewsets.ModelViewSet):
    queryset = PaymentInfo.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreatePaymentInfoSerializer
        return PaymentInfoSerializer


class StaffMemberViewSet(viewsets.ModelViewSet):
    queryset = (
        StaffMember.objects.select_related("user")
        .prefetch_related("services_offered")
        .all()
    )
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateStaffMemberSerializer
        return StaffMemberSerializer


class WorkingHoursViewSet(viewsets.ModelViewSet):
    queryset = WorkingHours.objects.all()
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrReadOnly]


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminOrReadOnly]


class BranchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateBranchSerializer
        return BranchSerializer

    def get_queryset(self):
        organization_pk = self.kwargs.get("organization_pk")
        queryset = Branch.objects.all()
        if organization_pk:
            return queryset.filter(organization_id=organization_pk)
        return queryset


class ServiceCounterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateServiceCounterSerializer
        return ServiceCounterSerializer

    def get_queryset(self):
        branch_pk = self.kwargs.get("branch_pk")
        queryset = ServiceCounter.objects.select_related(
            "staff_member", "service", "branch"
        ).all()
        if branch_pk:
            return queryset.filter(branch_id=branch_pk)
        return queryset
