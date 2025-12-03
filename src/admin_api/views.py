# admin_api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from accounts.models import User

from admin_api.serializers import AdminUserSerializer, AdminUserUpdateSerializer
from admin_api.filters import AdminUserFilter


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related().order_by("-date_joined")
    permission_classes = [IsAdminUser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = AdminUserFilter
    search_fields = ("username", "email", "first_name", "last_name")
    ordering_fields = ("username", "email")
    ordering = "username"

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return AdminUserUpdateSerializer
        return AdminUserSerializer

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(
            {
                "status": "Пользователь деактивирован",
                "user_id": user.id,
                "is_active": user.is_active,
            }
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response(
            {
                "status": "Пользователь активирован",
                "user_id": user.id,
                "is_active": user.is_active,
            }
        )

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
