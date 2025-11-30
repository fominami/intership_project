from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from salons.models import Salon, SalonCar
from salons.serializers import (
    SalonSerializer,
    SalonCreateSerializer,
    SalonCarSerializer,
)
from salons.permissions import SalonPermission, SalonCarPermission
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from salons.filters import SalonFilter, SalonCarFilter
from rest_framework.response import Response


class SalonViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Salon.objects.all()
    serializer_class = SalonSerializer
    permission_classes = [SalonPermission]

    def get_serializer_class(self):
        if self.action == "create":
            return SalonCreateSerializer
        return SalonSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SalonFilter
    search_fields = ("name", "address")
    ordering = ("name",)


class SalonCarViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SalonCar.objects.all()
    serializer_class = SalonCarSerializer
    permission_classes = [SalonCarPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = SalonCarFilter
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

    @action(detail=True, methods=["post"])
    def increase_count(self, request, pk=None):
        salon_car = self.get_object()
        count = request.data.get("count", 1)
        salon_car.count += count
        salon_car.save()
        return Response({"count": salon_car.count})

    @action(detail=True, methods=["post"])
    def decrease_count(self, request, pk=None):
        salon_car = self.get_object()
        count = request.data.get("count", 1)
        if salon_car.count >= count:
            salon_car.count -= count
            salon_car.save()
            return Response({"count": salon_car.count})
        return Response({"error": "Недостаточно автомобилей"}, status=400)
