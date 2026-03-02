from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from api.models import Client


User = get_user_model()


class NationalIDBackend(BaseBackend):
    """
    Authenticate using Client.national_id instead of username.
    """

    def authenticate(self, request, national_id=None, password=None, **kwargs):
        if national_id is None or password is None:
            return None

        try:
            client = Client.objects.select_related("user").get(national_id=national_id)
        except Client.DoesNotExist:
            return None

        user = client.user

        if user.check_password(password) and user.is_active:
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
