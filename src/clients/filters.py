import django_filters
from clients.models import Client


class ClientFilter(django_filters.FilterSet):
    username = django_filters.CharFilter()

    class Meta:
        model = Client
        fields = ["username"]
