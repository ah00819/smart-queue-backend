from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.serializers import BaseAddressSerializer, ClientSerializer
from api.models import Address, Client
from .models import SMSVerificationCode, User
from rest_framework import serializers
from phonenumber_field.modelfields import PhoneNumberField

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
    verification_token = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "client", "verification_token"]

    def validate(self, attrs):
        token = attrs.pop("verification_token", None)
        client_data = attrs.get("client", {})
        phone_number = client_data.get("phone")

        if phone_number:
            phone_str = str(phone_number)
            if Client.objects.filter(phone=phone_number).exists():
                raise serializers.ValidationError(
                    {"client": {"phone": "This phone number is already registered."}}
                )
            if not token:
                raise serializers.ValidationError(
                    {"verification_token": "A verification token is required when providing a phone number."}
                )
            sms_record = SMSVerificationCode.objects.filter(
                session_token=token, phone=phone_str, is_verified=True, is_used=False
            ).last()
            if not sms_record or sms_record.is_expired():
                raise serializers.ValidationError(
                    {"verification_token": "Phone number registration session is invalid or expired."}
                )
            attrs["_sms_record"] = sms_record
        else:
            attrs["_sms_record"] = None
            
        return attrs

    def create(self, validated_data):
        sms_record = validated_data.pop("_sms_record", None)
        client_data = validated_data.pop("client")
        address_data = client_data.pop("address", None)

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            address = Address.objects.create(**address_data) if address_data else None
            Client.objects.create(user=user, address=address, **client_data)

            if sms_record:
                sms_record.user = user
                sms_record.is_used = True
                sms_record.save()
                
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

class RequestSMSCodeSerializer(serializers.Serializer):
    phone = PhoneNumberField()


class VerifySMSCodeSerializer(serializers.Serializer):
    phone = PhoneNumberField()
    code = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.ChoiceField(choices=["register", "reset_password"])

    def validate(self, attrs):
        phone = attrs.get("phone")
        code = attrs.get("code")
        purpose = attrs.get("purpose")

        if purpose == "reset_password" and not Client.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "No registered user found with this number."})
            
        if purpose == "register" and Client.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({"phone": "This phone number is already registered."})

        # Find code record linked to the phone number directly
        sms_record = SMSVerificationCode.objects.filter(
            phone=phone, code=code, is_used=False, is_verified=False
        ).last()

        if not sms_record:
            raise serializers.ValidationError({"code": "Invalid verification code."})

        if sms_record.is_expired():
            sms_record.is_used = True
            sms_record.save()
            raise serializers.ValidationError({"code": "This code has expired. Request a new one."})

        attrs["sms_record"] = sms_record
        return attrs


class SetNewPasswordSerializer(serializers.Serializer):
    session_token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate(self, attrs):
        token = attrs.get("session_token")
        
        # Ensure the token matches a verified, unexpired session that hasn't been closed/used yet
        sms_record = SMSVerificationCode.objects.filter(
            session_token=token, is_verified=True, is_used=False
        ).last()

        if not sms_record or sms_record.is_expired():
            raise serializers.ValidationError({"session_token": "Session invalid or expired. Restart the process."})

        attrs["sms_record"] = sms_record
        attrs["user"] = sms_record.user
        return attrs