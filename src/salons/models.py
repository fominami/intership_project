from django.db import models
from django.core.validators import MinValueValidator
from common.models import Base
# from django.contrib.gis.db import models as gis_models


class SalonCar(Base):
    salon = models.ForeignKey("Salon", on_delete=models.CASCADE)
    car = models.ForeignKey("cars.Car", on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ["salon", "car"]


class Salon(Base):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        # limit_choices_to={'role': User.Role.SALON}
    )
    name = models.CharField(max_length=250)
    address = models.TextField()
    # location = gis_models.PointField(blank=True, null=True)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )
    cars = models.ManyToManyField(
        "cars.Car", through="SalonCar", through_fields=("salon", "car")
    )

    def __str__(self):
        return self.name
