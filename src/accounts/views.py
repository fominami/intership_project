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
from django.utils.http import urlsafe_base64_encode
import secrets
from accounts.serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordEmailSerializer,
    ResetPasswordConfirmSerializer,
    UpdateProfileSerializer,
)

User = get_user_model()


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
            {"status": "Your account has been deactivated."},
            status=status.HTTP_204_NO_CONTENT,
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
        return Response({"message": "Email confirmed!"})
    except (User.DoesNotExist, ValueError):
        return Response({"error": "Invalid token"}, status=400)


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

        return Response({"message": "Password changed successfully"})


@api_view(["POST"])
def reset_password_email(request):
    """Отправка ссылки для сброса пароля"""
    serializer = ResetPasswordEmailSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "User with such email already exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Сохраняем в cache
        cache.set(f"reset_token_{uid}", token, 3600)

        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        send_mail(
            "Password reset",
            f"Перейдите по ссылке: {reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

        return Response({"message": "Password reset link has been sent."})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def reset_password_confirm(request, uidb64, token):
    """Подтверждение сброса пароля"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid link"}, status=status.HTTP_400_BAD_REQUEST)

    cached_token = cache.get(f"reset_token_{uidb64}")
    if cached_token != token:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ResetPasswordConfirmSerializer(data=request.data)
    if serializer.is_valid():
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        cache.delete(f"reset_token_{uidb64}")
        return Response({"message": "Password reset"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UpdateProfileSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if new_email := serializer.validated_data.get("new_email"):
            cache.set(f"pending_email_{user.id}", new_email, 3600)
            token = secrets.token_urlsafe(32)
            cache.set(f"profile_email_confirm_{token}", user.id, 3600)
            send_mail(
                "Confirming new email",
                f"Подтвердите: {settings.FRONTEND_URL}/confirm-profile-update/{token}/",
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
            )

        if new_username := serializer.validated_data.get("new_username"):
            cache.set(f"pending_username_{user.id}", new_username, 3600)
            token = secrets.token_urlsafe(32)
            cache.set(f"profile_username_confirm_{token}", user.id, 3600)

        return Response(
            {"message": "Confirmation links have been sent to a new email address."}
        )


@api_view(["GET"])
def confirm_profile_update(request, token):
    """Подтверждение и применение изменений username/email"""
    email_user_id = cache.get(f"profile_email_confirm_{token}")
    username_user_id = cache.get(f"profile_username_confirm_{token}")

    user_id = email_user_id or username_user_id
    field_type = "email" if email_user_id else "username"

    if not user_id:
        return Response({"error": "Invalid token"}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    if field_type == "email":
        pending_email = cache.get(f"pending_email_{user.id}")
        if pending_email:
            user.email = pending_email
            cache.delete(f"pending_email_{user.id}")

    elif field_type == "username":
        pending_username = cache.get(f"pending_username_{user.id}")
        if pending_username:
            user.username = pending_username
            cache.delete(f"pending_username_{user.id}")

    user.save()
    cache.delete(f"profile_{field_type}_confirm_{token}")

    return Response(
        {
            "message": f"{field_type.capitalize()} successfully updated!",
            "user_id": user.id,
        }
    )
