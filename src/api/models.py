from django.db import models

# from django.contrib.gis.db import models as gis_models
from django.contrib.auth.models import User  # , Group

# salon_group, created = Group.objects.get_or_create(name="salon")
# client_group, created = Group.objects.get_or_create(name="client")
# supplier_group, created = Group.objects.get_or_create(name="supplier")


# ManyToMany Tables
class SalonCar(models.Model):
    salon = models.ForeignKey("Salon", on_delete=models.CASCADE)
    car = models.ForeignKey("Car", on_delete=models.CASCADE)
    number = models.IntegerField(null=False)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["salon", "car"]


class PromotionSalon(models.Model):
    promotion = models.ForeignKey("Promotion", on_delete=models.CASCADE)
    salon = models.ForeignKey("Salon", on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["promotion", "salon"]


class PromotionCar(models.Model):
    promotion = models.ForeignKey("Promotion", on_delete=models.CASCADE)
    car = models.ForeignKey("Car", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["promotion", "car"]


class SupplierCar(models.Model):
    supplier = models.ForeignKey("Supplier", on_delete=models.CASCADE)
    car = models.ForeignKey("Car", on_delete=models.CASCADE)
    price = models.IntegerField(null=False)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["supplier", "car"]


class Car(models.Model):
    brand = models.CharField(max_length=250)
    model = models.CharField(max_length=250)
    characteristic = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.brand} {self.model}"


class Salon(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    address = models.TextField()
    # location = gis_models.PointField(blank=True, null=True)
    balance = models.IntegerField()
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    cars = models.ManyToManyField(
        Car, through="SalonCar", through_fields=("salon", "car")
    )

    def __str__(self):
        return self.name


class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    foundation_year = (
        models.IntegerField()
    )  # можно добавить валидаторы, чтобы год не был больше текущего
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    cars = models.ManyToManyField(
        Car, through="SupplierCar", through_fields=("supplier", "car")
    )

    def __str__(self):
        return self.name


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    info = models.JSONField(blank=True, null=True)
    balance = models.IntegerField()
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Promotion(models.Model):
    name = models.CharField(max_length=250)
    info = models.JSONField(blank=True, null=True)
    start = models.DateTimeField()
    end = (
        models.DateTimeField()
    )  # можно поставить проверку, чтобы было не раньше начала
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    salons = models.ManyToManyField(
        Salon,
        through="PromotionSalon",
        through_fields=("promotion", "salon"),
        related_name="salon_promotions",
    )
    cars = models.ManyToManyField(
        Car,
        through="PromotionCar",
        through_fields=("promotion", "car"),
        related_name="car_promotions",
    )

    def __str__(self):
        return self.name


# Othermodels
class Preference(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="preferences"
    )
    category = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client", "category"]

    def __str__(self):
        return f"{self.client}: {self.category}"


class Deal(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name="deals")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="deals")
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="deals"
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="deals")
    sum = models.IntegerField()
    is_active = models.BooleanField(default=True)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["client", "sum"]

    def __str__(self):
        return f"Deal #{self.id} - {self.sum}"
