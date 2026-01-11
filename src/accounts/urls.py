from django.urls import path
from accounts import views

urlpatterns = [
    path(
        "profile/",
        views.ProfileViewSet.as_view(
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
        "profile/stats/",
        views.ProfileViewSet.as_view({"get": "stats"}),
        name="profile_stats",
    ),
    path(
        "",
        views.PublicUserViewSet.as_view({"get": "list"}),
        name="public_users_list",  # ✅ snake_case
    ),
    path(
        "<int:pk>/",
        views.PublicUserViewSet.as_view({"get": "retrieve"}),
        name="public_user_detail",
    ),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("confirm-email/<str:token>/", views.confirm_email, name="confirm_email"),
    path(
        "change-password/", views.ChangePasswordView.as_view(), name="change_password"
    ),
    path(
        "reset-password-email/", views.reset_password_email, name="reset_password_email"
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        views.reset_password_confirm,
        name="reset_password_confirm",
    ),
]
