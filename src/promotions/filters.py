import django_filters
from promotions.models import Promotion, PromotionCar, PromotionSalon


class PromotionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter(method="filter_active")

    def filter_active(self, queryset, name, value):
        from django.utils import timezone

        now = timezone.now()
        if value:
            return queryset.filter(started_at__lte=now, ended_at__gte=now)
        return queryset.filter(ended_at__lt=now) | queryset.filter(started_at__gt=now)

    class Meta:
        model = Promotion
        fields = ()


class PromotionCarFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(field_name="car__brand", lookup_expr="icontains")
    model = django_filters.CharFilter(field_name="car__model", lookup_expr="icontains")

    class Meta:
        model = PromotionCar
        fields = ()


class PromotionSalonFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="salon__name", lookup_expr="icontains")
    address = django_filters.CharFilter(
        field_name="salon__address", lookup_expr="icontains"
    )
    min_balance = django_filters.NumberFilter(
        field_name="salon__balance", lookup_expr="gte"
    )
    max_balance = django_filters.NumberFilter(
        field_name="salon__balance", lookup_expr="lte"
    )
    min_discount = django_filters.NumberFilter(field_name="discount", lookup_expr="gte")
    max_discount = django_filters.NumberFilter(field_name="discount", lookup_expr="lte")

    class Meta:
        model = PromotionSalon
        fields = ()
