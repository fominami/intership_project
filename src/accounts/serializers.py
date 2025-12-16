from rest_framework import serializers
from accounts.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model


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


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.Role.choices)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password", "role")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.send_confirmation_email()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль неверный")
        return value


class ResetPasswordEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email не найден")
        return value


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


class UpdateProfileSerializer(serializers.ModelSerializer):
    new_email = serializers.EmailField(required=False, allow_blank=True)
    new_username = serializers.CharField(required=False, allow_blank=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ("new_email", "new_username", "current_password")

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль")
        return value

    def validate_new_email(self, value):
        if (
            value
            and User.objects.filter(email=value)
            .exclude(id=self.context["request"].user.id)
            .exists()
        ):
            raise serializers.ValidationError("Email уже используется")
        return value

    def validate_new_username(self, value):
        if (
            value
            and User.objects.filter(username=value)
            .exclude(id=self.context["request"].user.id)
            .exists()
        ):
            raise serializers.ValidationError("Username уже используется")
        return value


class ConfirmProfileUpdateSerializer(serializers.Serializer):
    token = serializers.CharField()
    field = serializers.ChoiceField(choices=["email", "username"])
