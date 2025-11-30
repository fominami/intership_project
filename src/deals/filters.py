import django_filters
from deals.models import Deal


class DealFilter(django_filters.FilterSet):
    min_sum = django_filters.NumberFilter(field_name="sum", lookup_expr="gte")
    max_sum = django_filters.NumberFilter(field_name="sum", lookup_expr="lte")
    salon_name = django_filters.CharFilter(
        field_name="salon__name", lookup_expr="icontains"
    )
    client_username = django_filters.CharFilter(
        field_name="client__user__username", lookup_expr="icontains"
    )
    car_brand = django_filters.CharFilter(
        field_name="car__make", lookup_expr="icontains"
    )

    class Meta:
        model = Deal
        fields = []
