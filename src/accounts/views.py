from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    PublicUserSerializer,
)
from accounts.models import User


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
