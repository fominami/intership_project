from django.db import models
from common.models import Base


class CarModels(models.TextChoices):
    TOYOTA = "TOYOTA", "Toyota"
    HONDA = "HONDA", "Honda"
    BMW = "BMW", "BMW"
    MERCEDES = "MERCEDES", "Mercedes-Benz"
    AUDI = "AUDI", "Audi"


class Car(Base):
    brand = models.CharField(max_length=250)
    model = models.CharField(max_length=25, choices=CarModels.choices)
    characteristic = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.brand} {self.model}"
