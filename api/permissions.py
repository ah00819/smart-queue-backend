from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import STAFF_GROUP
from appointment.models import Appointment, AppointmentRequest


def is_staff_member(user):
    """Returns whether the user belongs to the Service Staff Member Group"""
    return user.groups.filter(name=STAFF_GROUP).exists()


class IsOwner(BasePermission):
    """Allow access only to the object owner."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsOwnerOrAdmin(BasePermission):
    """Owner has access; admin has full access."""

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """Admins can write; everyone can read."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_staff


class AppointmentPermissions(BasePermission):
    """
    Admin: full access
    Staff: access assigned appointments
    Client: access own appointments
    """

    def has_object_permission(self, request, view, obj: Appointment):
        user = request.user

        if user.is_staff:
            return True

        if is_staff_member(user):
            return obj.appointment_request.staff_member.user == user

        return obj.appointment_request.client == user


class AppointmentRequestPermissions(BasePermission):
    """
    Admin: full access
    Staff: access assigned requests
    Client: access own requests
    """

    def has_object_permission(self, request, view, obj: AppointmentRequest):
        user = request.user

        if user.is_staff:
            return True

        if is_staff_member(user):
            return obj.staff_member.user == user

        if hasattr(obj, "appointment"):
            return obj.appointment.client == user

        return True


class IsStaffMemberOrAdminOrReadOnly(BasePermission):
    """
    Read: everyone authenticated
    Write:
      - Admin: all
      - Staff: own only
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_staff or is_staff_member(request.user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        return obj.staff_member.user == request.user
