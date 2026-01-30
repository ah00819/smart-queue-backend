from rest_framework.viewsets import ModelViewSet
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

from api.pagenation import DefaultPagination
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
    CreateServiceCounterSerializer,
    CreateStaffMemberSerializer,
    DayOffSerializer,
    ReadWriteSerializerMixin,
    StaffMemberSerializer,
    WorkingHoursSerializer,
    ServiceSerializer,
    OrganizationSerializer,
    BranchSerializer,
    ServiceCounterSerializer,
)

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


class AppointmentRequestViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, AppointmentRequestPermissions]
    pagination_class = DefaultPagination

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

    def get_serializer_class(self):
        if self.action == "create":
            return CreateAppointmentRequestSerializer
        return AppointmentRequestSerializer


class AppointmentViewSet(ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, AppointmentPermissions]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.select_related("appointment_request")
        if user.is_staff:
            return queryset

        if user.groups.filter(name="Service Staff Member").exists():
            return queryset.filter(appointment_request__staff_member__user=user)

        return queryset.filter(client=user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)


class ConfigViewSet(ModelViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [IsAdminUser]


class DayOffViewSet(ModelViewSet):
    serializer_class = DayOffSerializer
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]

    def get_queryset(self):
        staff_member_pk = self.kwargs.get("staff_member_pk")
        queryset = DayOff.objects.select_related("staff_member", "staff_member__user")
        if staff_member_pk:
            return queryset.filter(staff_member_id=staff_member_pk)
        return queryset

    def perform_create(self, serializer):
        staff_member_pk = self.kwargs.get("staff_member_pk")
        if staff_member_pk:
            serializer.save(staff_member_id=staff_member_pk)
        else:
            serializer.save()


class WorkingHoursViewSet(ModelViewSet):
    queryset = WorkingHours.objects.all()
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]

    def get_queryset(self):
        queryset = WorkingHours.objects.all()
        staff_member_pk = self.request.query_params.get("staff_member_pk")
        if staff_member_pk:
            queryset.filter(staff_member_pk=staff_member_pk)
        return queryset

    def perform_create(self, serializer):
        staff_member_pk = self.kwargs.get("staff_member_pk")
        if staff_member_pk:
            serializer.save(staff_member_id=staff_member_pk)
        else:
            serializer.save()


class StaffMemberViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = StaffMemberSerializer
    write_serializer = CreateStaffMemberSerializer
    queryset = (
        StaffMember.objects.select_related("user")
        .prefetch_related("services_offered")
        .all()
    )
    permission_classes = [IsAuthenticated, IsStaffMemberOrAdminOrReadOnly]
    pagination_class = DefaultPagination


class ServiceViewSet(ModelViewSet):
    queryset = Service.objects.all()
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
        organization_pk = self.kwargs.get("organization_pk")
        queryset = Branch.objects.all()
        if organization_pk:
            return queryset.filter(organization_id=organization_pk)
        return queryset


class ServiceCounterViewSet(ReadWriteSerializerMixin, ModelViewSet):
    read_serializer = ServiceCounterSerializer
    write_serializer = CreateServiceCounterSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination

    def get_queryset(self):
        branch_pk = self.kwargs.get("branch_pk")
        queryset = ServiceCounter.objects.select_related(
            "staff_member", "service", "branch"
        )
        return queryset.filter(branch_id=branch_pk) if branch_pk else queryset
