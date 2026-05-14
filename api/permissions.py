from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import STAFF_GROUP, Appointment


def is_staff_member(user):
    """Returns whether the user belongs to the Service Staff Member Group"""
    return user.groups.filter(name=STAFF_GROUP).exists()


class IsOwner(BasePermission):
    """Allow access only to the object owner."""

    def has_object_permission(self, request, view, obj):
        user_attr = getattr(obj, "user", None)
        return user_attr == request.user


class IsOwnerOrAdmin(BasePermission):
    """Owner has access; admin has full access."""

    def has_object_permission(self, request, view, obj):
        user_attr = getattr(obj, "user", None)
        return request.user.is_staff or user_attr == request.user


class IsAdminOrReadOnly(BasePermission):
    """Admins can write; everyone can read."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or request.user.is_staff


class AppointmentPermissions(BasePermission):
    """
    Admin: full access
    Staff: access appointments assigned to their counter
    Client: access own appointments
    """

    def has_object_permission(self, request, view, obj: Appointment):
        user = request.user

        if user.is_staff:
            return True

        if is_staff_member(user):
            return (
                obj.counter
                and obj.counter.staff_member
                and obj.counter.staff_member.user == user
            )

        return obj.client and obj.client.user == user


class IsStaffMemberOrAdminOrReadOnly(BasePermission):
    """
    Read: everyone authenticated
    Write:
      - Admin: all
      - Staff: own only (WorkDays, LeaveRequests)
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

        return hasattr(obj, "staff_member") and obj.staff_member.user == request.user
