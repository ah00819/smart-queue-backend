from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
import pytest
from model_bakery import baker

from api.models import Address, Client

User = get_user_model()


@pytest.fixture
def create_client(api_client):
    def do_create_client(client):
        return api_client.post("/api/clients/", client)

    return do_create_client


@pytest.mark.django_db
class TestCreateClient:
    def test_if_user_is_anonymous_return_401(
        self, create_client, authenticate, api_client
    ):
        user = authenticate()

        # Un-authenticate
        api_client.force_authenticate(user=None)

        client = {
            "user": user,
            "national_id": "01234567891011",
        }

        response = create_client(client)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_client_already_exists_return_400(self, authenticate, create_client):
        user = authenticate()
        client_data = {"national_id": "01234567891011"}

        create_client(client_data)

        response = create_client(client_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_if_data_is_invalid_return_400(self, authenticate, create_client):
        user = authenticate()

        client = {"national_id": "0234567891013"}

        response = create_client(client)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "national_id" in response.data

    def test_if_data_is_valid_return_201(self, authenticate, create_client):
        user = authenticate()
        national_id = "01234567891011"

        client = {
            "user": user.id,
            "national_id": national_id,
        }

        response = create_client(client)

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestListClient:
    def test_if_user_is_anonymous_return_401(self, api_client):
        response = api_client.get("/api/clients/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Business-logic
    def test_if_user_is_authorized_list_own_clients_return_200(
        self, authenticate, api_client
    ):
        user = authenticate()
        baker.make(Client, user=user)

        baker.make(Client)

        response = api_client.get("/api/clients/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["user"] == user.id

    def test_if_user_is_admin_list_all_return_200(self, authenticate, api_client):
        user_dummy = authenticate()
        baker.make(Client, user=user_dummy)

        authenticate(is_staff=True)

        response = api_client.get("/api/clients/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) != 0


@pytest.mark.django_db
class TestRetrieveClient:
    def test_if_client_exists_return_200(self, authenticate, api_client):
        user = authenticate()
        client = baker.make(Client, user=user)

        response = api_client.get(f"/api/clients/{client.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": client.id,
            "user": user.id,
            "address": client.address,
            "national_id": client.national_id,
            "birth_date": client.birth_date,
            "profession": client.profession,
            "gender": client.gender,
            "image": client.image,
        }

    def test_if_client_does_not_exists_return_404(self, authenticate, api_client):
        authenticate()

        response = api_client.get("/api/clients/1/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] is not None


@pytest.mark.django_db
class TestDeleteClient:
    def test_if_user_is_anonymous_return_401(self, authenticate, api_client):
        user = authenticate()
        client = baker.make(Client, user=user)

        # Un-authenticate
        api_client.force_authenticate(user=None)

        response = api_client.delete(f"/api/clients/{client.id}/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_owner_return_204(self, authenticate, api_client):
        user = authenticate()
        client = baker.make(Client, user=user)

        response = api_client.delete(f"/api/clients/{client.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_user_is_admin_return_204(self, authenticate, api_client):
        user = authenticate()
        client = baker.make(Client, user=user)

        authenticate(is_staff=True)

        response = api_client.delete(f"/api/clients/{client.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_user_is_not_owner_return_404(self, authenticate, api_client):
        user = authenticate()
        client = baker.make(Client, user=user)

        authenticate()

        response = api_client.delete(f"/api/clients/{client.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
