from django.urls import path
from accounts.views import ProfileViewSet, PublicUserViewSet

urlpatterns = [
    path(
        "profile/",
        ProfileViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="profile",
    ),
    path(
        "profile/stats/", ProfileViewSet.as_view({"get": "stats"}), name="profile-stats"
    ),
    path("", PublicUserViewSet.as_view({"get": "list"}), name="public-users-list"),
    path(
        "<int:pk>/",
        PublicUserViewSet.as_view({"get": "retrieve"}),
        name="public-user-detail",
    ),
]
