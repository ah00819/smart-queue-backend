from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import datetime

from api.models import Appointment, Notification


def create_notification(client, title, body):
    Notification.objects.create(
        client=client,
        title=title,
        body=body
    )


def send_reminders():
    now = timezone.now()

    appointments = Appointment.objects.filter(
        canceled=False,
        want_reminder=True,
    )

    for appointment in appointments:
        appointment_datetime = timezone.make_aware(
            datetime.combine(
                appointment.date,
                appointment.start_time
            )
        )

        diff = appointment_datetime - now

        total_minutes = int(diff.total_seconds() / 60)

        # Reminder before 24 hours
        if (
            1439 <= total_minutes <= 1441
            and not appointment.reminder_24_sent
        ):
            create_notification(
                appointment.client,
                "Appointment Reminder",
                "Your appointment is after 24 hours."
            )

            appointment.reminder_24_sent = True
            appointment.save()

        # Reminder before 1 hour
        if (
            59 <= total_minutes <= 61
            and not appointment.reminder_1h_sent
        ):
            create_notification(
                appointment.client,
                "Appointment Reminder",
                "Your appointment is after 1 hour."
            )

            appointment.reminder_1h_sent = True
            appointment.save()


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_reminders, 'interval', minutes=1)
    scheduler.start()