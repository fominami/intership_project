import django_filters
from suppliers.models import Supplier, SupplierCar


class SupplierFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    fondation_date = django_filters.DateFilter()

    class Meta:
        model = Supplier
        fields = ()


class SupplierCarFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(field_name="car__brand", lookup_expr="icontains")
    model = django_filters.CharFilter(field_name="car__model", lookup_expr="icontains")

    class Meta:
        model = SupplierCar
        fields = ()
