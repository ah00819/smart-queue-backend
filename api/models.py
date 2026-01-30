from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from appointment.models import StaffMember, Service
from phonenumber_field.modelfields import PhoneNumberField
from .validators import ExactLengthValidator, validate_birth_date, validate_file_size

# Create your models here.


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


class Client(models.Model):
    """
    user => ($username, $password, first_name, last_name, email)
    $username = full_name = first_name + last_name
    address, $card_id, birth_date, proffesion, gender, Image
    """

    GENDER_MALE = "M"
    GENDER_FEMALE = "F"

    GENDER_CHOICES = [(GENDER_MALE, "Male"), (GENDER_FEMALE, "Female")]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, unique=True
    )
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
    is_authenticated = models.BooleanField(
        default=False, verbose_name=_("Is Authenticated")
    )

    def __str__(self):
        return self.user

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

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")


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
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branches")
        unique_together = ("organization", "name")


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
        on_delete=models.SET_NULL,
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

        if self.staff_member and self.service:
            if not self.staff_member.services_offered.filter(
                id=self.service_id
            ).exists():
                raise ValidationError(
                    "The assigned staff member does not offer this service."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
