from django.db import models
from django.core.exceptions import ValidationError
from common.models import Base


class PromotionSalon(Base):
    promotion = models.ForeignKey("Promotion", on_delete=models.CASCADE)
    salon = models.ForeignKey("salons.Salon", on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ["promotion", "salon"]


class PromotionCar(Base):
    promotion = models.ForeignKey("Promotion", on_delete=models.CASCADE)
    car = models.ForeignKey("cars.Car", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["promotion", "car"]


class Promotion(Base):
    name = models.CharField(max_length=250)
    info = models.JSONField(blank=True, null=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    salons = models.ManyToManyField(
        "salons.Salon",
        through="PromotionSalon",
        through_fields=("promotion", "salon"),
        related_name="salon_promotions",
    )
    cars = models.ManyToManyField(
        "cars.Car",
        through="PromotionCar",
        through_fields=("promotion", "car"),
        related_name="car_promotions",
    )

    def clean(self):
        if self.started_at and self.ended_at and self.started_at >= self.ended_at:
            raise ValidationError(
                {"ended_at": "Время окончания должно быть позже времени начала"}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
