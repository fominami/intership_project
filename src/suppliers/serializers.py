from rest_framework import serializers
from suppliers.models import Supplier, SupplierCar
from cars.serializers import CarSerializer


class SupplierSerializer(serializers.BaseSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    name = serializers.CharField(max_length=250)
    foundation_date = serializers.DateField()

    class Meta:
        model = Supplier
        fields = ("id", "user", "name", "foundation_date")


class SupplierCarSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)

    class Meta:
        model = SupplierCar
        fields = ("id", "car", "price")


class SupplierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("name", "foundation_date")
