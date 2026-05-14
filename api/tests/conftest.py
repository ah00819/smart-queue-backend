from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
import pytest
from model_bakery import baker

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate(api_client):
    def do_authenticate(user=None, is_staff: bool = False) -> User | None:
        if user is None:
            user = baker.make(User, is_staff=is_staff)

        api_client.force_authenticate(user=user)
        return user

    return do_authenticate
