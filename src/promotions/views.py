from rest_framework import viewsets, mixins
from promotions.models import Promotion, PromotionSalon, PromotionCar
from promotions.serializers import (
    PromotionSerializer,
    PromotionSalonSerializer,
    PromotionCarSerializer,
)
from promotions.permissions import (
    PromotionPermission,
    PromotionSalonPermission,
    PromotionCarPermission,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from promotions.filters import PromotionFilter, PromotionSalonFilter, PromotionCarFilter


class PromotionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [PromotionPermission]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PromotionFilter
    search_fields = "name"
    ordering_fields = ("name", "started_at", "ended_at")
    ordering = "name"


class PromotionSalonViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PromotionSalon.objects.all()
    serializer_class = PromotionSalonSerializer
    permission_classes = [PromotionSalonPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PromotionSalonFilter
    search_fields = ("salon__name", "salon__address")
    ordering_fields = ("discount", "salon__name")
    ordering = "name"

    def get_queryset(self):
        queryset = super().get_queryset()

        promotion_id = self.kwargs.get("promotion_pk")
        if promotion_id:
            queryset = queryset.filter(promotion_id=promotion_id)
        return queryset

    def perform_create(self, serializer):
        promotion_id = self.kwargs.get("promotion_pk")
        if promotion_id:
            serializer.save(promotion_id=promotion_id)
        else:
            serializer.save()


class PromotionCarViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = PromotionCar.objects.all()
    serializer_class = PromotionCarSerializer
    permission_classes = [PromotionCarPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PromotionCarFilter
    search_fields = ("car__brand", "car__model")
    ordering_fields = ("car__brand", "car__model")
    ordering = "car__brand"

    def get_queryset(self):
        queryset = super().get_queryset()

        promotion_id = self.kwargs.get("promotion_pk")
        if promotion_id:
            queryset = queryset.filter(promotion_id=promotion_id)

        return queryset

    def perform_create(self, serializer):
        promotion_id = self.kwargs.get("promotion_pk")
        if promotion_id:
            serializer.save(promotion_id=promotion_id)
        else:
            serializer.save()
