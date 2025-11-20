from django.db import models
from common.models import Base
from django.core.validators import MinValueValidator


class Deal(Base):
    salon = models.ForeignKey(
        "salons.Salon", on_delete=models.CASCADE, related_name="deals"
    )
    car = models.ForeignKey("cars.Car", on_delete=models.CASCADE, related_name="deals")
    supplier = models.ForeignKey(
        "suppliers.Supplier", on_delete=models.CASCADE, related_name="deals"
    )
    client = models.ForeignKey(
        "clients.Client", on_delete=models.CASCADE, related_name="deals"
    )
    sum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    class Meta:
        ordering = ["client", "sum"]

    def __str__(self):
        return f"Deal #{self.id} - {self.sum}"
