import datetime
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from .validators import ExactLengthValidator, validate_birth_date, validate_file_size
from datetime import datetime, timedelta

# Create your models here.

STAFF_GROUP = "Service Staff Member"


class Address(models.Model):
    address = models.CharField(max_length=255, verbose_name=_("Street Address"))
    city = models.CharField(max_length=100, verbose_name=_("City"))
    country = models.CharField(max_length=100, verbose_name=_("Country"))
    postal_code = models.CharField(
        max_length=20, null=True, blank=True, verbose_name=_("Postal Code")
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Latitude"),
        help_text=_("GPS Latitude"),
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_("Longitude"),
        help_text=_("GPS Longitude"),
    )

    def __str__(self) -> str:
        return f"{self.address}, {self.city}, {self.country}"

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        unique_together = (("latitude", "longitude"), ("address", "city", "country"))


class ProfileMixin(models.Model):
    GENDER_MALE = "M"
    GENDER_FEMALE = "F"

    GENDER_CHOICES = [(GENDER_MALE, "Male"), (GENDER_FEMALE, "Female")]
    address = models.OneToOneField(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Address"),
    )
    national_id = models.CharField(
        max_length=14,
        unique=True,
        verbose_name=_("National ID"),
        validators=[ExactLengthValidator(14)],
    )
    birth_date = models.DateField(
        verbose_name=_("Birth Date"),
        null=True,
        blank=True,
        validators=[validate_birth_date],
    )
    phone = PhoneNumberField(
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Contact phone number"),
    )
    profession = models.CharField(
        max_length=100, verbose_name=_("Profession"), null=True, blank=True
    )
    gender = models.CharField(
        max_length=1, choices=GENDER_CHOICES, null=True, blank=True
    )
    image = models.ImageField(
        upload_to="api/clients/images",
        validators=[validate_file_size],
        null=True,
        blank=True,
        verbose_name=_("Client Image"),
    )

    class Meta:
        abstract = True


class Client(ProfileMixin):
    """
    user => ($username, $password, first_name, last_name, email)
    $username = full_name = first_name + last_name
    address, $card_id, birth_date, proffesion, gender, Image
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True
    )
    is_authenticated = models.BooleanField(
        default=False, verbose_name=_("Is Authenticated")
    )

    def __str__(self) -> str:
        return self.user.__str__()

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name=_("Name"))
    code = models.CharField(max_length=50, unique=True, verbose_name="Code")
    brief = models.TextField(null=True, blank=True, verbose_name=_("Brief"))
    image = models.ImageField(
        upload_to="api/organizations/images",
        validators=[validate_file_size],
        null=True,
        blank=True,
        verbose_name=_("Image"),
    )
    email = models.EmailField(null=True, blank=True, verbose_name=("Email"))
    website = models.URLField(null=True, blank=True, verbose_name=_("Website"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")

    def __str__(self) -> str:
        return self.name


class WorkDay(models.Model):
    WEEKDAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]
    # staff_member = models.ForeignKey(
    #     StaffMember, related_name="workdays", on_delete=models.CASCADE
    # )
    weekday = models.IntegerField(choices=WEEKDAYS)
    from_hour = models.TimeField()
    to_hour = models.TimeField()

    class Meta:
        verbose_name = _("Work Day/Operating Hour")

    def __str__(self):
        return f"{self.get_weekday_display()}: {self.from_hour}-{self.to_hour}"

    def get_weekday_display(self) -> str:
        return next(
            (day for idx, day in self.WEEKDAYS if idx == self.weekday), "Unknown Day"
        )


class StaffMember(ProfileMixin):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True
    )
    services_offered = models.ManyToManyField(
        "Service",
        verbose_name=_("Services Offered"),
        help_text=_("Services that this staff member provides."),
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name=_("Organization"),
        related_name="staff_members",
    )
    workdays = models.ManyToManyField(
        WorkDay,
        related_name="staff_members",
        blank=True,
        verbose_name=_("Staff Working Hours"),
    )

    class Meta:
        verbose_name = _("Staff Member")
        verbose_name_plural = _("Staff Members")
        unique_together = ("user", "organization")

    def __str__(self) -> str:
        return self.user.__str__()


class Service(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="services",
        verbose_name=_("Oraganization"),
    )
    name = models.CharField(max_length=100, blank=False, verbose_name=_("Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    duration = models.DurationField(
        validators=[MinValueValidator(timedelta(minutes=1))],
        verbose_name=_("Duration"),
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_("Price"),
    )
    image = models.ImageField(
        upload_to="api/services/images",
        blank=True,
        null=True,
        verbose_name=_("Service Image"),
    )
    currency = models.CharField(
        max_length=3,
        default="EGP",
        validators=[ExactLengthValidator(3)],
        verbose_name=_("Currency"),
    )
    reschedule_limit = models.PositiveIntegerField(
        default=0,
        help_text=_("Maximum number of times an appointment can be rescheduled."),
        verbose_name=_("Reschedule limit"),
    )

    # meta data
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def can_reschedule(self) -> bool:
        return self.reschedule_limit > 0

    def get_price_text(self) -> str:
        return f"{self.price} {self.currency}"

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["name"]  # alphabetical by default
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return self.name


class Branch(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="branches",
        verbose_name=_("Oraganization"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    address = models.OneToOneField(
        Address, on_delete=models.PROTECT, verbose_name=_("Address")
    )
    email = models.EmailField(null=True, blank=True, verbose_name=("Email"))
    phone = PhoneNumberField(
        null=True,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Contact phone number"),
    )
    operating_hours = models.ManyToManyField(
        WorkDay,
        related_name="branches",
        blank=True,
        verbose_name=_("Branch Operating Hours"),
    )
    services = models.ManyToManyField(
        Service,
        blank=True,
        related_name="branch_services",
        help_text=_("Branch offered Services"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        unique_together = ("organization", "name")

    def __str__(self) -> str:
        return self.name

    def clean(self):
        super().clean()


class ServiceCounter(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name="service_counters",
        verbose_name=_("Branch"),
    )
    staff_member = models.ForeignKey(
        StaffMember,
        on_delete=models.RESTRICT,
        null=True,
        related_name="counter",
        verbose_name=_("Staff Member"),
        help_text=_("Staff member assigned to this counter"),
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name="counters",
        verbose_name=_("Service"),
        help_text=_("Service this counter offers"),
    )
    is_operational = models.BooleanField(default=True, verbose_name=_("Is Operational"))

    def __str__(self):
        return f"{self.name} offers {self.service}"

    class Meta:
        verbose_name = _("Service Counter")
        verbose_name_plural = _("Service Counters")

    def clean(self):
        super().clean()
        if self.branch and self.service:
            if not self.branch.services.filter(id=self.service_id).exists():
                raise ValidationError(
                    _("This service is not available at this branch.")
                )
        if (
            self.staff_member
            and self.service
            and not self.staff_member.services_offered.filter(
                id=self.service_id
            ).exists()
        ):
            raise ValidationError(
                "The assigned staff member does not offer this service."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_available_slots(self, date):
        # Check for Holidays
        if Holiday.objects.filter(date=date).exists():
            return []

        # Check for Staff Leave Requests
        leave = LeaveRequest.objects.filter(
            staff_member=self.staff_member, date=date
        ).first()
        if leave and leave.is_full_day:
            return []

        # Get Work Hours for this weekday
        weekday = date.weekday()  # 0=Monday
        work_day = self.staff_member.workdays.filter(weekday=weekday).first()
        if not work_day:
            return []

        # Generate potential slots based on Service Duration
        slots = []
        service_duration = self.service.duration
        current_time = datetime.combine(date, work_day.from_hour)
        end_work_time = datetime.combine(date, work_day.to_hour)

        # Fetch existing appointments to check for overlaps
        existing_appointments = Appointment.objects.filter(
            counter=self, date=date
        ).values_list("start_time", "end_time")

        slot_number = 1
        while current_time + service_duration <= end_work_time:
            slot_start = current_time.time()
            slot_end = (current_time + service_duration).time()
            # Check if this slot overlaps with any existing appointment
            is_busy = any(
                not (slot_end <= app_start or slot_start >= app_end)
                for app_start, app_end in existing_appointments
            )
            if not is_busy:
                slots.append(
                    {
                        "number": slot_number,
                        "start": slot_start.strftime("%H:%M"),
                        "end": slot_end.strftime("%H:%M"),
                    }
                )
                slot_number += 1
            current_time += service_duration

        return slots


# New Model Replacement of django-appointments


class LeaveRequest(models.Model):
    """
    Handles specific days off, sick leave, or vacations.
    """

    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    is_full_day = models.BooleanField(default=True)


class Holiday(models.Model):
    """
    Global holidays where the whole business is closed.
    """

    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)


class Appointment(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Client"),
        help_text=_("The user who made the appointment request."),
    )
    # --- Time Slot ---
    date = models.DateField(
        verbose_name=_("Date"), help_text=_("The date of the appointment request.")
    )
    start_time = models.TimeField(
        verbose_name=_("Start Time"),
        help_text=_("The start time of the appointment request."),
    )
    end_time = models.TimeField(
        verbose_name=_("End Time"),
        help_text=_("The end time of the appointment request."),
    )
    slot_number = models.PositiveIntegerField(
        verbose_name=_("Slot Number"), 
        null=True, 
        blank=True
    )
    # -----------------
    counter = models.ForeignKey(
        ServiceCounter,
        on_delete=models.RESTRICT,
        null=True,
        verbose_name=_("Service Counter"),
    )
    reschedule_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Reschedule Attempts"),
        help_text=_("Number of times this appointment has been rescheduled."),
    )
    want_reminder = models.BooleanField(
        default=False,
        verbose_name=_("Want Reminder"),
        help_text=_(
            "Indicates whether the client wants a reminder for the appointment."
        ),
    )

    reminder_24_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)

    additional_info = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Additional Info"),
        help_text=_(
            "Any additional information the client wants to provide for the appointment."
        ),
    )

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", _("Cash")
        CREDIT = "CREDIT", _("Credit Card")
        DEBIT = "DEBIT", _("Debit Card")
        ONLINE = "ONLINE", _("Online Payment")

    paid = models.BooleanField(
        default=False,
        verbose_name=_("Paid"),
        help_text=_("Indicates whether the appointment has been paid for."),
    )
    amount_to_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Amount to Pay"),
        help_text=_(
            "The amount to be paid for the appointment. "
            "If 0, it means the appointment is free or already paid."
        ),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        null=True,
        verbose_name=_("Payment Method"),
        help_text=_("The method used to pay for the appointment."),
    )

    canceled = models.BooleanField(default=False, verbose_name=_("Canceled"))
    # this is used to add penalties on the client later
    missed = models.BooleanField(
        default=False,
        verbose_name=_("Missed"),
        help_text=_("Missed the Appointment time"),
    )
    # meta datas
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["date", "start_time"]),
            models.Index(fields=["counter", "date"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount_to_pay__gte=0), name="positive_amount_to_pay"
            )
        ]

    def __str__(self):
        return (
            f"{self.client} - "
            f"{self.start_time.strftime('%Y-%m-%d %H:%M')} to "
            f"{self.end_time.strftime('%Y-%m-%d %H:%M')}"
        )


class ServiceFeedback(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name=_("Client"),
        help_text=_("Client writing the feedback"),
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.RESTRICT,
        verbose_name=_("Appointment"),
        help_text=_("Appointment the Feedback is on"),
    )
    feedback = models.TextField(
        verbose_name=_("Review"),
        help_text=_("Write Feedback to the Service Appointment"),
    )

    class Meta:
        verbose_name = _("Service Feedback")
        verbose_name_plural = _("Service Feedbacks")
        unique_together = ("client", "appointment")


class RequiredDocument(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="required_documents",
        verbose_name=_("Service"),
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Document Name"),
        help_text=_("e.g. Identity Card, Proof of Address"),
    )
    description = models.TextField(
        blank=True, null=True, verbose_name=_("Document Description")
    )
    is_mandatory = models.BooleanField(default=True, verbose_name=_("Is Mandatory"))

    def __str__(self):
        return f"{self.name} for {self.service.name}"

    class Meta:
        verbose_name = _("Required Document")
        verbose_name_plural = _("Required Documents")
        unique_together = ("service", "name")


def get_upload_path(instance, filename):
    return f"appointment/{instance.appointment.id}/documents/{filename}"


class AttachedDocument(models.Model):
    STATUS_CHOICES = [
        ("pending", _("Pending Review")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
    ]
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="attached_documents"
    )
    document = models.ForeignKey(RequiredDocument, on_delete=models.SET_NULL, null=True)
    file = models.FileField(
        upload_to=get_upload_path,
        validators=[validate_file_size],
        verbose_name=_("File"),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Appointment Document")
        verbose_name_plural = _("Appointment Documents")


class Notification(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client} - {self.title}"
