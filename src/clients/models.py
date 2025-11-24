from django.db import models
from common.models import Base
from django.core.validators import MinValueValidator


class Client(Base):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        # limit_choices_to={'role': User.Role.CLIENT}
    )
    info = models.JSONField(blank=True, null=True)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    def __str__(self):
        return self.user.username


class Preference(Base):
    client = models.ForeignKey(
        "Client", on_delete=models.CASCADE, related_name="preferences"
    )
    category = models.CharField(max_length=100)
    value = models.CharField(max_length=100)

    class Meta:
        ordering = ["client", "category"]

    def __str__(self):
        return f"{self.client}: {self.category}"
