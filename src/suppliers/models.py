from django.db import models
from common.models import Base
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime


class SupplierCar(Base):
    supplier = models.ForeignKey("Supplier", on_delete=models.CASCADE)
    car = models.ForeignKey("cars.Car", on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    class Meta:
        unique_together = ["supplier", "car"]


class Supplier(Base):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        # limit_choices_to={'role': User.Role.SUPPLIER}
    )
    name = models.CharField(max_length=250)
    foundation_year = models.DateField(
        validators=[MaxValueValidator(datetime.date.today())]
    )
    cars = models.ManyToManyField(
        "cars.Car", through="SupplierCar", through_fields=("supplier", "car")
    )

    @property
    def year(self):
        """Получить только год"""
        return self.foundation_year.year

    def __str__(self):
        return self.name
