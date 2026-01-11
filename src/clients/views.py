from rest_framework import viewsets, mixins
from clients.models import Client
from clients.serializers import ClientSerializer, ClientCreateSerializer
from clients.permissions import ClientPermission
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from clients.filters import ClientFilter


class ClientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [ClientPermission]

    def get_serializer_class(self):
        if self.action == "create":
            return ClientCreateSerializer
        return ClientSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ClientFilter
    search_fields = "username"
    ordering = "model"
