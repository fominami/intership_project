from rest_framework import viewsets, mixins, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str, force_bytes
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User
from django.utils.http import urlsafe_base64_encode
import secrets
from django.utils.crypto import constant_time_compare
from accounts.serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordEmailSerializer,
    ResetPasswordConfirmSerializer,
    UpdateProfileSerializer,
    ConfirmProfileUpdateSerializer,
)


class ProfileViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def update(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def partial_update(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response(
            {"status": "Ваш аккаунт деактивирован"}, status=status.HTTP_204_NO_CONTENT
        )


class PublicUserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        return (
            User.objects.filter(is_active=True)
            .exclude(id=self.request.user.id)
            .order_by("username")
        )


User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@api_view(["GET"])
def confirm_email(request, token):
    # Полный ключ с токеном
    try:
        user_id = cache.get(f"email_confirm_{token}")
        if not user_id:
            raise ValueError("Токен не найден")
        user = User.objects.get(id=user_id)
        user.is_email_verified = True
        user.save()
        cache.delete(f"email_confirm_{token}")
        return Response({"message": "Email подтвержден!"})
    except (User.DoesNotExist, ValueError):
        return Response({"error": "Неверный токен"}, status=400)


class ChangePasswordView(generics.UpdateAPIView):
    """Смена пароля (требует старый пароль)"""

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.context["request"] = self.request
        return serializer

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"message": "Пароль успешно изменен"})


@api_view(["POST"])
def reset_password_email(request):
    """Отправка ссылки для сброса пароля"""
    serializer = ResetPasswordEmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Сохраняем в cache
        cache.set(f"reset_token_{uid}", token, 3600)

        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        send_mail(
            "Сброс пароля",
            f"Перейдите по ссылке: {reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

        return Response({"message": "Ссылка для сброса пароля отправлена"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def reset_password_confirm(request, uidb64, token):
    """Подтверждение сброса пароля"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {"error": "Неверная ссылка"}, status=status.HTTP_400_BAD_REQUEST
        )

    cached_token = cache.get(f"reset_token_{uidb64}")
    if cached_token != token:
        return Response({"error": "Неверный токен"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ResetPasswordConfirmSerializer(data=request.data)
    if serializer.is_valid():
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        cache.delete(f"reset_token_{uidb64}")
        return Response({"message": "Пароль сброшен"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(generics.UpdateAPIView):
    """Запрос на изменение username/email"""

    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        changes = {}

        if serializer.validated_data.get("new_email"):
            token = secrets.token_urlsafe(32)
            cache.set(f"profile_email_confirm_{token}", user.id, 3600)
            send_mail(
                "Подтверждение новой почты",
                f"Подтвердите новый email: {settings.FRONTEND_URL}/confirm-email-change/{token}/",
                settings.DEFAULT_FROM_EMAIL,
                [serializer.validated_data["new_email"]],
            )
            changes["email"] = "Ссылка отправлена"

        if serializer.validated_data.get("new_username"):
            token = secrets.token_urlsafe(32)
            cache.set(f"profile_username_confirm_{token}", user.id, 3600)
            changes["username"] = "Ссылка отправлена"

        return Response(
            {"message": "Ссылки для подтверждения отправлены", "changes": changes}
        )


@api_view(["GET"])
def confirm_profile_update(request, token):
    """Подтверждение изменения username/email"""
    field_token = None

    # Проверяем email token
    cached_user_id = cache.get(f"profile_email_confirm_{token}")
    if cached_user_id:
        field_token = "email"
    else:
        # Проверяем username token
        cached_user_id = cache.get(f"profile_username_confirm_{token}")
        if cached_user_id:
            field_token = "username"

    if not field_token or not cached_user_id:
        return Response({"error": "Неверный токен"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=cached_user_id)
    except User.DoesNotExist:
        return Response(
            {"error": "Пользователь не найден"}, status=status.HTTP_400_BAD_REQUEST
        )

    cache.set(f"pending_{field_token}_{user.id}", token, 3600)
    cache.delete(f"profile_{field_token}_confirm_{token}")

    return Response(
        {
            "message": f"{field_token.capitalize()} подтвержден!",
            "next_step": f"/api/accounts/apply-{field_token}-change/",
        }
    )


@api_view(["POST"])
def apply_email_change(request):
    """Применить изменение email после подтверждения"""
    serializer = ConfirmProfileUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data["token"]
    cached_token = cache.get(f"pending_email_{request.user.id}")

    if not constant_time_compare(token, cached_token):
        return Response(
            {"error": "Токен не подтвержден"}, status=status.HTTP_400_BAD_REQUEST
        )

    cache.delete(f"pending_email_{request.user.id}")
    return Response({"message": "Email обновлен!"})


@api_view(["POST"])
def apply_username_change(request):
    """Применить изменение username после подтверждения"""
    serializer = ConfirmProfileUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token = serializer.validated_data["token"]
    cached_token = cache.get(f"pending_username_{request.user.id}")

    if not constant_time_compare(token, cached_token):
        return Response(
            {"error": "Токен не подтвержден"}, status=status.HTTP_400_BAD_REQUEST
        )

    cache.delete(f"pending_username_{request.user.id}")
    return Response({"message": "Username обновлен!"})
