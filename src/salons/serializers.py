from rest_framework import serializers
from salons.models import Salon, SalonCar
from cars.serializers import CarSerializer


class SalonSerializer(serializers.BaseSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    cars_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Salon
        fields = ("id", "user", "name", "address", "balance")


class SalonCarSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)

    class Meta:
        model = SalonCar
        fields = ("id", "car", "count")


class SalonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salon
        fields = ("name", "address", "balance")
