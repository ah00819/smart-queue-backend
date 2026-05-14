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
from django.conf import settings
from PIL import Image
import google.generativeai as genai
import json
import io
from rest_framework.views import APIView

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
        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()

        if user.is_staff:
            return User.objects.all()

        return User.objects.filter(pk=user.pk)

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


# إعداد Gemini
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