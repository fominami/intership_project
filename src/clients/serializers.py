from rest_framework import serializers
from clients.models import Client


class ClientSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Client
        fields = ("id", "username", "email", "balance")


class ClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "balance"
