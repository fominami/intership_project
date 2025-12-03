import django_filters
from accounts.models import User


class AdminUserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="icontains")
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")

    role = django_filters.ChoiceFilter(choices=User.Role.choices)

    class Meta:
        model = User
        fields = []
