from rest_framework import viewsets, mixins, permissions
from rest_framework.decorators import action
from cars.models import Car
from cars.serializers import CarSerializer
from cars.permissions import CarPermission
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from cars.filters import CarFilter
from rest_framework.response import Response


class CarViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Car.objects.all()
    serializer_class = CarSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [CarPermission()]

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        car = self.get_object()
        car.is_active = False
        car.save()
        return Response({"status": "deactivated"})

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CarFilter
    search_fields = ("brand", "model")
    ordering_fields = ("brand", "model")
    ordering = "model"
