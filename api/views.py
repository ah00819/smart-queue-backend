from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
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
from .permissions import IsAdminOrReadOnly
from .models import Organization, Address, Branch, ServiceCounter
from .serializers import (
    AppointmentRequestSerializer,
    CreateAppointmentRequestSerializer,
    AppointmentSerializer,
    ConfigSerializer,
    CreateBranchSerializer,
    CreateDayOffSerializer,
    CreateServiceCounterSerializer,
    DayOffSerializer,
    PaymentInfoSerializer,
    StaffMemberSerializer,
    WorkingHoursSerializer,
    ServiceSerializer,
    OrganizationSerializer,
    AddressSerializer,
    BranchSerializer,
    ServiceCounterSerializer,
)

# Create your views here.


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     user = self.request.user
    #     return Appointment.objects.filter(client__id=user.id)


class AppointmentRequestViewSet(viewsets.ModelViewSet):
    queryset = (
        AppointmentRequest.objects.select_related("service")
        .select_related("staff_member")
        .all()
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateAppointmentRequestSerializer
        return AppointmentRequestSerializer


class ConfigViewSet(viewsets.ModelViewSet):
    queryset = Config.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [IsAuthenticated]


class DayOffViewSet(viewsets.ModelViewSet):
    queryset = DayOff.objects.select_related("staff_member").all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateDayOffSerializer
        return DayOffSerializer


class PaymentInfoViewSet(viewsets.ModelViewSet):
    queryset = PaymentInfo.objects.all()
    serializer_class = PaymentInfoSerializer
    permission_classes = [IsAuthenticated]


class StaffMemberViewSet(viewsets.ModelViewSet):
    queryset = StaffMember.objects.all()
    serializer_class = StaffMemberSerializer
    permission_classes = [IsAuthenticated]


class WorkingHoursViewSet(viewsets.ModelViewSet):
    queryset = WorkingHours.objects.all()
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAdminOrReadOnly]


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateBranchSerializer
        return BranchSerializer


class ServiceCounterViewSet(viewsets.ModelViewSet):
    queryset = ServiceCounter.objects.select_related(
        "staff_member", "service", "branch"
    ).all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateServiceCounterSerializer
        return ServiceCounterSerializer
