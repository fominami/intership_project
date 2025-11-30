from rest_framework import viewsets, mixins
from deals.models import Deal
from deals.permissions import DealPermission
from deals.serializers import DealSerializer
from deals.filters import DealFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class DealViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Deal.objects.all()
    permission_classes = [DealPermission]
    serializer_class = DealSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = DealFilter
    search_fields = ["salon__name", "client__user__username", "car__make", "car__model"]
    ordering_fields = ["sum", "created_at", "car__price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user.is_salon:
            return queryset.filter(salon__user=user)
        elif user.is_supplier:
            return queryset.filter(supplier__user=user)
        elif user.is_client:
            return queryset.filter(client__user=user)

        return queryset
