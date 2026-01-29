from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
import pytest
from model_bakery import baker

from appointment.models import Appointment, AppointmentRequest

User = get_user_model()


@pytest.fixture
def create_appointment(api_client):
    def do_create_appointment(appointment):
        return api_client.post("/api/appointments/", appointment)

    return do_create_appointment


@pytest.mark.django_db
class TestCreateAppointment:
    def test_if_user_is_anonymous_return_401(self, create_appointment):

        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )

        appointment = {
            "client": 1,
            "appointment_request": appointment_request.id,
            "phone": "+2001152123722",
            "address": "1234, Main, st, city",
            "want_reminder": True,
            "paid": False,
            "amount_to_pay": 20,
        }

        response = create_appointment(appointment)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_data_is_invalid_return_400(self, authenticate, create_appointment):
        authenticate()
        appointment = {}

        response = create_appointment(appointment)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "appointment_request" in response.data

    def test_if_data_is_valid_return_201(self, authenticate, create_appointment):
        user = authenticate()

        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )

        appointment = {
            "client": user,
            "appointment_request": appointment_request.id,
            "phone": "+2001152123722",
            "address": "1234, Main, st, city",
            "want_reminder": True,
            "paid": False,
            "amount_to_pay": 20,
        }

        response = create_appointment(appointment)
        assert response.status_code == status.HTTP_201_CREATED

    # Business-logic
    def test_if_appointment_exist_for_request_return_400(
        self, authenticate, create_appointment
    ):
        """User Duplicated Appointment Test"""
        user = authenticate()

        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )

        appointment = {
            "client": user.id,
            "appointment_request": appointment_request.id,
            "phone": "+2001152123722",
            "address": "1234, Main, st, city",
            "want_reminder": True,
            "paid": False,
            "amount_to_pay": 20,
        }

        first_res = create_appointment(appointment)
        assert first_res.status_code == status.HTTP_201_CREATED

        response = create_appointment(appointment)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "appointment_request" in response.data


@pytest.mark.django_db
class TestListAppointment:
    def test_if_user_is_anonymous_return_401(self, api_client):
        response = api_client.get("/api/appointments/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_authenticated_return_200(self, authenticate, api_client):
        authenticate()

        response = api_client.get("/api/appointments/")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestRetrieveAppointment:
    def test_if_appointment_exists_return_200(self, authenticate, api_client):
        user = authenticate()
        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        appointment = baker.make(
            Appointment,
            client=user,
            appointment_request=appointment_request,
        )

        response = api_client.get(f"/api/appointments/{appointment.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {
            "id": appointment.id,
            "client": user.id,
            "appointment_request": appointment_request.id,
            "phone": appointment.phone,
            "address": appointment.address,
            "want_reminder": appointment.want_reminder,
            "additional_info": appointment.additional_info,
            "paid": appointment.paid,
            "amount_to_pay": appointment.amount_to_pay,
            "id_request": appointment.id_request,
        }

    def test_if_appointment_does_not_exists_return_404(self, authenticate, api_client):
        authenticate()
        response = api_client.get("/api/appointments/0/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] is not None


@pytest.mark.django_db
class TestDeleteAppointment:
    def test_if_user_is_anonymous_return_401(self, authenticate, api_client):
        user = authenticate()
        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        appointment = baker.make(
            Appointment,
            client=user,
            appointment_request=appointment_request,
        )

        # Un-authenticate
        api_client.force_authenticate(user=None)

        response = api_client.delete(f"/api/appointments/{appointment.id}/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_if_user_is_owner_return_204(self, authenticate, api_client):
        user = authenticate()
        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        appointment = baker.make(
            Appointment,
            client=user,
            appointment_request=appointment_request,
        )

        response = api_client.delete(f"/api/appointments/{appointment.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_user_is_staff_assigned_return_204(self, authenticate, api_client):
        user = authenticate()
        staff_member_user = baker.make(User)

        staff_group, _ = Group.objects.get_or_create(name="Service Staff Member")
        staff_member_user.groups.add(staff_group)

        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        staff_member = baker.make("appointment.StaffMember", user=staff_member_user)
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            staff_member=staff_member,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        appointment = baker.make(
            Appointment,
            client=user,
            appointment_request=appointment_request,
        )

        # Switch to Staff Member
        api_client.force_authenticate(user=staff_member_user)

        response = api_client.delete(f"/api/appointments/{appointment.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_user_is_admin_return_204(self, authenticate, api_client):
        user = authenticate()
        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        appointment = baker.make(
            Appointment,
            client=user,
            appointment_request=appointment_request,
        )

        # Switch to Admin
        admin = baker.make(User, is_staff=True)
        api_client.force_authenticate(user=admin)

        response = api_client.delete(f"/api/appointments/{appointment.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_if_user_is_not_owner_return_404(self, authenticate, api_client):
        user = authenticate()
        service = baker.make("appointment.Service", duration=timedelta(minutes=60))
        appointment_request = baker.make(
            AppointmentRequest,
            service=service,
            date=date.today(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        appointment = baker.make(
            Appointment,
            client=user,
            appointment_request=appointment_request,
        )

        # Switch to Random user
        user = baker.make(User)
        api_client.force_authenticate(user=user)

        response = api_client.delete(f"/api/appointments/{appointment.id}/")

        # 404 and not 403; because i'm doing a queryset filter before passed to permission
        assert response.status_code == status.HTTP_404_NOT_FOUND
