from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admin Only Have All access otherwise you can
    use SAFE_METHODS 'GET,OPTION,HEAD'
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class AppointmentPermissions(permissions.BasePermission):
    """
    Used in Appointment and AppointmentRequest Model Views
    admin-users: full control
    staff: full control over assigned appointments only.
    authenticated: full control over their own appointments only.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.user.groups.filter(name="Service Staff Member").exists():
            return obj.appointment_request.staff_member.user == request.user

        return obj.client == request.user


class AppointmentRequestPermissions(permissions.BasePermission):
    """
    Used in Appointment and AppointmentRequest Model Views
    admin-users: full control
    staff: full control over assigned appointments only.
    authenticated: full control over their own appointments only.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.user.groups.filter(name="Service Staff Member").exists():
            return obj.staff_member.user == request.user

        return obj.client == request.user


class IsStaffMemberOrAdminOrReadOnly(permissions.BasePermission):
    """
    Used in DaysOff Model View
    admin: full control.
    staff: full control over OWN, view others.
    authenticated: view only.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user.is_staff
            or request.user.groups.filter(name="Service Staff Member").exists()
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        return obj.staff_member.user == request.user
