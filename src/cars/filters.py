import django_filters
from cars.models import Car


class CarFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter()
    model = django_filters.CharFilter()

    class Meta:
        model = Car
        fields = ["brand", "model"]
