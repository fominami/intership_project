from rest_framework import serializers
from salons.serializers import SalonSerializer
from cars.serializers import CarSerializer
from promotions.models import Promotion, PromotionSalon, PromotionCar


class PromotionSerializer(serializers.BaseSerializer):
    name = serializers.CharField(max_length=250)
    info = serializers.JSONField()
    started_at = serializers.DateTimeField()
    ended_at = serializers.DateTimeField()

    class Meta:
        model = Promotion
        fields = ("name", "info", "started_at", "ended_at")


class PromotionCarSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)

    class Meta:
        model = PromotionCar
        fields = ("id", "car")


class PromotionSalonSerializer(serializers.ModelSerializer):
    salon = SalonSerializer(read_only=True)

    class Meta:
        model = PromotionSalon
        fields = ("id", "salon")
