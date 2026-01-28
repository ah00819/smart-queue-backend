from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()
router.register("appointments", views.AppointmentViewSet, basename="appointments")
router.register(
    "appointment-requests",
    views.AppointmentRequestViewSet,
    basename="appointment-requests",
)
router.register("configs", views.ConfigViewSet, basename="configs")
router.register("days-off", views.DayOffViewSet, basename="days-off")
router.register("payment-infos", views.PaymentInfoViewSet, basename="payment-infos")
router.register("staff-members", views.StaffMemberViewSet, basename="staff-members")
router.register("working-hours", views.WorkingHoursViewSet, basename="working-hours")
router.register("services", views.ServiceViewSet, basename="services")
router.register("organizations", views.OrganizationViewSet, basename="organizations")
router.register("branches", views.BranchViewSet, basename="branches")
router.register(
    "service-counters", views.ServiceCounterViewSet, basename="service-counters"
)

urlpatterns = router.urls
