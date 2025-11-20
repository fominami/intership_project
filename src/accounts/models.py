from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Покупатель"
        SALON = "SALON", "Автосалон"
        SUPPLIER = "SUPPLIER", "Поставщик"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=25, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_salon(self):
        return self.role == self.Role.SALON

    @property
    def is_supplier(self):
        return self.role == self.Role.SUPPLIER
