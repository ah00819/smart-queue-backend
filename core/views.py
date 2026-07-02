import uuid

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from api.models import Client
from .models import SMSVerificationCode, User
from .serializers import (
    NationalIDTokenSerializer,
    CreateProfileSerializer,
    RequestSMSCodeSerializer,
    SetNewPasswordSerializer,
    SimpleProfileSerializer,
    UpdateProfileSerializer,
    VerifySMSCodeSerializer,
)
from django.conf import settings
from PIL import Image
import google.generativeai as genai
import json
import io
from rest_framework.views import APIView
from core.utils import send_sms_message
from django.db import transaction
# Create your views here.

# accounts/views.py


class ProfileViewSet(viewsets.ModelViewSet):

    def initial(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            self.http_method_names = ["post", "head", "options"]
        else:
            self.http_method_names = ["get", "put", "patch", "delete", "head", "options"]
            # dirty fix, 'options' is currenty useless
            if self.action == "me":
                self.http_method_names.remove("options")

        return super().initial(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()

        if user.is_staff:
            return User.objects.all()

        return User.objects.filter(pk=user.pk)

    def get_serializer_class(self):
        # Handle SMS actions
        if self.action in ["reset_password_request", "register_sms_request"]:
            return RequestSMSCodeSerializer
        
        if self.action == "verify_sms_code":
            return VerifySMSCodeSerializer
            
        if self.action == "reset_password_confirm":
            return SetNewPasswordSerializer

        # CRUD actions
        if self.action == "create":
            return CreateProfileSerializer
        
        if self.action in ["update", "partial_update", "me"]:
            # GET on /profiles/me/
            if self.request.method == "GET":
                return SimpleProfileSerializer
            return UpdateProfileSerializer
        
        return SimpleProfileSerializer

    @action(detail=False, methods=["get", "put", "patch", "delete"], permission_classes=[IsAuthenticated])
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

    # register_sms_request (send code) -> verify_sms_code (verify)
    # reset_password_request (send code) -> verify_sms_code (verify) -> reset_password_confirm (reset password)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register_sms_request(self, request):
        """
        Registration Step 1: Verify number is unique, generate and send verification code.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data["phone"]
        
        if Client.objects.filter(phone=phone).exists():
            return Response(
                {"phone": "This phone number is already registered."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        verification = SMSVerificationCode.generate_code_for_phone(phone=phone)
        send_sms_message(phone_number=str(phone), message=f"*{verification.code}* is your Smart Queue verification code.")
        
        return Response(
            {"detail": "Verification code has been sent successfully via SMS."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def verify_sms_code(self, request):
        """
        Step 2 (Shared): Validates code for either Register or Reset contexts.
        Returns a session_token string used as secure clearance.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sms_record = serializer.validated_data["sms_record"]
        
        sms_record.is_verified = True
        sms_record.session_token = uuid.uuid4()
        sms_record.save()
        
        return Response(
            {
                "detail": "Code verified successfully.",
                "session_token": str(sms_record.session_token)
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def reset_password_request(self, request):
        """
        Password Reset Step 1: Send reset code if client profile is matched.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data["phone"]
        
        try:
            client = Client.objects.select_related("user").get(phone=phone)
            user_obj = client.user
        except Client.DoesNotExist:
            return Response(
                {"detail": "Verification code dispatched if account exists."}, 
                status=status.HTTP_200_OK
            )
        
        verification = SMSVerificationCode.generate_code_for_phone(phone=phone, user=user_obj)
        send_sms_message(phone_number=str(phone), message=f"*{verification.code}* is your Smart Queue password reset code.")
        
        return Response(
            {"detail": "Verification code has been successfully sent via SMS."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def reset_password_confirm(self, request):
        """
        3. If the token is authenticated, accept the submission to change the password.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data["user"]
        sms_record = serializer.validated_data["sms_record"]
        new_password = serializer.validated_data["new_password"]
        
        with transaction.atomic():
            user.set_password(new_password)
            user.save()
            
            sms_record.is_used = True
            sms_record.save()
            
        return Response(
            {"detail": "Your password has been changed successfully. You can now log in."},
            status=status.HTTP_200_OK
        )

class NationalIDTokenView(TokenObtainPairView):
    serializer_class = NationalIDTokenSerializer

# ID Card Info Extraction Using Gemini

genai.configure(api_key=settings.GEMINI_API_KEY)
class ExtractIDCardView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {'error': 'من فضلك ابعت صورة'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            image = Image.open(io.BytesIO(image_file.read()))
            model = genai.GenerativeModel('gemini-3-flash-preview')

            prompt = """
            هذه صورة بطاقة هوية مصرية.
            استخرج البيانات التالية وأرجعها كـ JSON فقط بدون أي نص إضافي:
            {
                "national_id": "الرقم القومي المكون من 14 رقم",
                "name_arabic": "الاسم بالعربي",
                "address": "العنوان كامل"
            }
            إذا لم تتمكن من قراءة أي حقل اكتب null
            """

            response = model.generate_content([prompt, image])
            response_text = response.text.strip()
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(response_text)

            missing_fields = []
            for field in ['national_id', 'name_arabic', 'address']:
                if not data.get(field) or data.get(field) == 'null':
                    missing_fields.append(field)

            if missing_fields:
                return Response({
                    'success': False,
                    'error': 'الصورة مش واضحة، صور تاني',
                    'missing_fields': missing_fields
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'success': True,
                'data': data
            }, status=status.HTTP_200_OK)

        except json.JSONDecodeError:
            return Response(
                {'error': 'فشل في قراءة البيانات من الصورة'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
