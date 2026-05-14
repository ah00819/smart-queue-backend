from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NationalIDTokenView, ProfileViewSet, ExtractIDCardView

router = DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")

urlpatterns = [
    path("login/", NationalIDTokenView.as_view(), name="login"),
    path("extract-id/", ExtractIDCardView.as_view(), name="extract-id"),
]

urlpatterns += router.urls