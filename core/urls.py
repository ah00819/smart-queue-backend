from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NationalIDTokenView, ProfileViewSet

router = DefaultRouter()
router.register("profiles", ProfileViewSet, basename="profiles")

urlpatterns = [
    path("login/", NationalIDTokenView.as_view(), name="login"),
]

urlpatterns += router.urls
