from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

import random
from datetime import timezone, timedelta
# Create your models here.


class User(AbstractUser):
    """Custom User"""


class SMSVerificationCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    phone = PhoneNumberField(verbose_name=_("Phone Number"), db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    session_token = models.UUIDField(default=None, null=True, blank=True, unique=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @classmethod
    def generate_code_for_phone(cls, phone, user=None):
        phone_str = str(phone)
        cls.objects.filter(phone=phone_str, is_used=False).update(is_used=True)
        
        code = f"{random.randint(100000, 999999)}"
        return cls.objects.create(user=user, phone=phone, code=code)