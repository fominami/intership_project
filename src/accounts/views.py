from rest_framework import viewsets, mixins, permissions
from accounts.models import User
from accounts.serializers import UserSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from accounts.filters import UserFilter


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "update":
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = UserFilter
    search_fields = ("username", "email", "first_name", "last_name")
    ordering_fields = ("username", "last_name")
    ordering = "username"
