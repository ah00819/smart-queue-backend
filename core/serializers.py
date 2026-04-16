from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.serializers import BaseAddressSerializer, ClientSerializer
from api.models import Address, Client
from .models import User


class CreateProfileClientSerializer(serializers.ModelSerializer):
    address = BaseAddressSerializer(required=False, allow_null=True)

    class Meta:
        model = Client
        fields = [
            "national_id",
            "birth_date",
            "phone",
            "profession",
            "gender",
            "address",
            "image",
        ]


class UpdateAddressSerializer(BaseAddressSerializer):
    class Meta(BaseAddressSerializer.Meta):
        validators = []

class UpdateProfileClientSerializer(serializers.ModelSerializer):
    address = UpdateAddressSerializer(required=False, allow_null=True)

    class Meta:
        model = Client
        fields = [
            "birth_date",
            "phone",
            "profession",
            "gender",
            "address",
            "image",
        ]


class SimpleProfileSerializer(serializers.ModelSerializer):
    client = ClientSerializer()

    class Meta:
        model = User
        fields = ["id", "username", "email", "client"]


class CreateProfileSerializer(serializers.ModelSerializer):
    """Grouping User data and Client Appointment-Api Specific Data"""

    client = CreateProfileClientSerializer()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "client"]

    def create(self, validated_data):
        client_data = validated_data.pop("client")
        address_data = client_data.pop("address", None)

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)

            address = Address.objects.create(**address_data) if address_data else None

            Client.objects.create(user=user, address=address, **client_data)
        return user


class UpdateProfileSerializer(serializers.ModelSerializer):
    client = UpdateProfileClientSerializer(required=False)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "email", "password", "client"]

    def update(self, instance, validated_data):
        client_data = validated_data.pop("client", None)
        password = validated_data.pop("password", None)

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if password:
                instance.set_password(password)
                instance.save()

            if client_data:
                address_data = client_data.pop("address", None)
                client_instance = instance.client

                for attr, value in client_data.items():
                    setattr(client_instance, attr, value)

                if address_data:
                    if client_instance.address:
                        for attr, value in address_data.items():
                            setattr(client_instance.address, attr, value)
                        client_instance.address.save()
                    else:
                        client_instance.address = Address.objects.create(**address_data)

                client_instance.save()

        return instance


class NationalIDTokenSerializer(TokenObtainPairSerializer):
    username_field = "national_id"

    def validate(self, attrs):
        national_id = attrs.get("national_id")
        password = attrs.get("password")

        try:
            client = Client.objects.select_related("user").get(national_id=national_id)
        except Client.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                "No client found with this National ID."
            )
        user = authenticate(
            request=self.context.get("request"),
            national_id=national_id,
            password=password,
        )
        if user is None:
            raise exceptions.AuthenticationFailed("Invalid password.")
        if not user.is_active:
            raise exceptions.AuthenticationFailed("User account is disabled.")

        attrs["username"] = client.user.username
        return super().validate(attrs)
