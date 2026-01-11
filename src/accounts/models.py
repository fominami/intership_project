from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Покупатель"
        SALON = "SALON", "Автосалон"
        SUPPLIER = "SUPPLIER", "Поставщик"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    email = models.EmailField(
        unique=True, verbose_name="Email", blank=False, null=False
    )
    phone = models.CharField(max_length=25, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def send_confirmation_email(self):  # ← ВНУТРИ класса!
        token = str(uuid.uuid4())
        cache.set("email_confirm_" + token, self.id, 86400)
        send_mail(
            "Подтверждение email",
            f"Ссылка: {settings.FRONTEND_URL}/confirm-email/{token}/",
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
        )

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_salon(self):
        return self.role == self.Role.SALON

    @property
    def is_supplier(self):
        return self.role == self.Role.SUPPLIER
