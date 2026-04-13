from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register("clients", views.ClientViewSet, basename="clients")
router.register("appointments", views.AppointmentViewSet, basename="appointments")
router.register("staff-members", views.StaffMemberViewSet, basename="staff-members")
router.register("services", views.ServiceViewSet, basename="services")
router.register("organizations", views.OrganizationViewSet, basename="organizations")
router.register("branches", views.BranchViewSet, basename="branches")
router.register(
    "service-counters", views.ServiceCounterViewSet, basename="service-counters"
)
# =================================================
organizations_router = routers.NestedDefaultRouter(
    router, "organizations", lookup="organization"
)
organizations_router.register(
    "branches", views.BranchViewSet, basename="organization-branches"
)
# =================================================
branches_router = routers.NestedDefaultRouter(router, "branches", lookup="branch")
branches_router.register(
    "service-counters", views.ServiceCounterViewSet, basename="branch-service-counters"
)
# =================================================
staff_members_router = routers.NestedDefaultRouter(
    router, "staff-members", lookup="staff_member"
)
staff_members_router.register(
    "work-days", views.WorkDayViewSet, basename="staff-member-work-days"
)
staff_members_router.register(
    "leave-requests", views.LeaveRequestViewSet, basename="staff-member-leave-requests"
)
# =================================================
service_router = routers.NestedSimpleRouter(router, "services", lookup="service")
service_router.register(
    "required-documents",
    views.RequiredDocumentViewSet,
    basename="service-required-documents",
)
# =================================================
appointment_router = routers.NestedSimpleRouter(
    router, "appointments", lookup="appointment"
)
appointment_router.register(
    "documents", views.AttachedDocumentViewSet, basename="appointment-documents"
)
appointment_router.register(
    "feedback", views.ServiceFeedbackViewSet, basename="appointment-feedback"
)
# =================================================


urlpatterns = (
    router.urls
    + organizations_router.urls
    + branches_router.urls
    + staff_members_router.urls
    + service_router.urls
    + appointment_router.urls
)
