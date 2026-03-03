from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import (
    NationalIDTokenSerializer,
    CreateProfileSerializer,
    SimpleProfileSerializer,
    UpdateProfileSerializer,
)

# Create your views here.

# accounts/views.py


class ProfileViewSet(viewsets.ModelViewSet):
    """
    Anonymous Users: return a serializer that allows POST only
    Authenticated Users: return a serializer that allows all but POST
    """

    def initial(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            self.http_method_names = ["post", "head", "options"]
        else:
            self.http_method_names = [
                "get",
                "put",
                "patch",
                "delete",
                "head",
                "options",
            ]
            # dirty fix, 'options' is currenty useless
            if self.action == "me":
                self.http_method_names.remove("options")

        return super().initial(request, *args, **kwargs)

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateProfileSerializer
        if self.action in ["update", "partial_update", "me"]:
            # GET on /profiles/me/
            if self.request.method == "GET":
                return SimpleProfileSerializer
            return UpdateProfileSerializer
        return SimpleProfileSerializer

    @action(detail=False, methods=["get", "put", "patch", "delete"])
    def me(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method in ["PUT", "PATCH"]:
            serializer = self.get_serializer(
                user, data=request.data, partial=(request.method == "PATCH")
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == "DELETE":
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class NationalIDTokenView(TokenObtainPairView):
    serializer_class = NationalIDTokenSerializer
