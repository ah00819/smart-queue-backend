from django.db import transaction
from rest_framework import serializers
from api.serializers import CreateProfileClientSerializer
from .models import User


class ProfileSerializer(serializers.ModelSerializer):
    """Grouping User data and Client Appointment-Api Specific Data"""

    client = CreateProfileClientSerializer()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "client"]

    def validate(self, attrs):
        user = self.context["request"].user
        if user.is_authenticated and self.context["request"].method == "POST":
            raise serializers.ValidationError(
                "Authenticated users cannot create a new profile."
            )
        return attrs

    def create(self, validated_data):
        client_data = validated_data.pop("client")

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            client_serializer = CreateProfileClientSerializer(
                data=client_data,
                context=self.context,
            )
            client_serializer.is_valid(raise_exception=True)
            client_serializer.save(user=user)
        return user

    def update(self, instance, validated_data):
        client_data = validated_data.pop("client", {})
        password = validated_data.pop("password", None)

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            if password:
                instance.set_password(password)
                instance.save()

            if client_data:
                client_instance = getattr(instance, "client", None)
                if client_instance:
                    for attr, value in client_data.items():
                        setattr(client_instance, attr, value)
                    client_instance.save()

        return instance
