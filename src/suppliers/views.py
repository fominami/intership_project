from rest_framework import viewsets, mixins
from suppliers.models import Supplier, SupplierCar
from suppliers.serializers import (
    SupplierSerializer,
    SupplierCreateSerializer,
    SupplierCarSerializer,
)
from suppliers.permissions import SupplierPermission, SupplierCarPermission
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from suppliers.filters import SupplierFilter, SupplierCarFilter


class SupplierViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [SupplierPermission]

    def get_serializer_class(self):
        if self.action == "create":
            return SupplierCreateSerializer
        return SupplierSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SupplierFilter
    search_fields = "name"
    ordering_fields = ("name", "price")
    ordering = "name"


class SupplierCarViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SupplierCar.objects.all()
    serializer_class = SupplierCarSerializer
    permission_classes = [SupplierCarPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SupplierCarFilter
    search_fields = ("brand", "model")
    ordering = "model"

    def get_queryset(self):
        queryset = super().get_queryset()

        salon_id = self.kwargs.get("salon_pk")
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)

        return queryset

    def perform_create(self, serializer):
        salon_id = self.kwargs.get("salon_pk")
        if salon_id:
            serializer.save(salon_id=salon_id)
        else:
            serializer.save()
