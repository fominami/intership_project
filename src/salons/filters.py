import django_filters
from salons.models import Salon, SalonCar


class SalonFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    address = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Salon
        fields = ()


class SalonCarFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(field_name="car__brand", lookup_expr="icontains")
    model = django_filters.CharFilter(field_name="car__model", lookup_expr="icontains")

    class Meta:
        model = SalonCar
        fields = ()
