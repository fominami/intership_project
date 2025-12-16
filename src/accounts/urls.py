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
        name="profile-stats",
    ),
    path(
        "", views.PublicUserViewSet.as_view({"get": "list"}), name="public-users-list"
    ),
    path(
        "<int:pk>/",
        views.PublicUserViewSet.as_view({"get": "retrieve"}),
        name="public-user-detail",
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
    path("update-profile/", views.UpdateProfileView.as_view(), name="update_profile"),
    path(
        "confirm-profile-update/<str:token>/",
        views.confirm_profile_update,
        name="confirm_profile_update",
    ),
    path("apply-email-change/", views.apply_email_change, name="apply_email_change"),
    path(
        "apply-username-change/",
        views.apply_username_change,
        name="apply_username_change",
    ),
]
