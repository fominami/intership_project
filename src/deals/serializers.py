from rest_framework import serializers
from deals.models import Deal


class DealSerializer(serializers.ModelSerializer):
    salon_name = serializers.CharField(source="salon.name", read_only=True)
    car_info = serializers.CharField(source="car.__str__", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    client_username = serializers.CharField(
        source="client.user.username", read_only=True
    )

    class Meta:
        model = Deal
        fields = (
            "id",
            "salon",
            "salon_name",
            "car",
            "car_info",
            "supplier",
            "supplier_name",
            "client",
            "client_username",
            "sum",
        )
