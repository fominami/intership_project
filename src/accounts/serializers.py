from rest_framework import serializers
from accounts.models import User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("Этот email уже используется")
        return value


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "role")
