from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register("clients", views.ClientViewSet, basename="clients")
router.register("appointments", views.AppointmentViewSet, basename="appointments")
router.register(
    "appointment-requests",
    views.AppointmentRequestViewSet,
    basename="appointment-requests",
)
router.register("configs", views.ConfigViewSet, basename="configs")
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
    "service-counters", views.ServiceCounterViewSet, basename="branch-service-coutners"
)
# =================================================
staff_members_router = routers.NestedDefaultRouter(
    router, "staff-members", lookup="staff_member"
)
staff_members_router.register(
    "working-hours", views.WorkingHoursViewSet, basename="staff-member-working-hours"
)
staff_members_router.register(
    "days-off", views.DayOffViewSet, basename="staff-member-days-off"
)
# =================================================

urlpatterns = (
    router.urls
    + organizations_router.urls
    + branches_router.urls
    + staff_members_router.urls
)
