from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Настройки для drf-yasg
schema_view = get_schema_view(
    openapi.Info(
        title="Internship Project API",
        default_version="v1",
        description="API for internship project",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def home(request):
    return HttpResponse(
        """
        <h1>Django API работает!</h1>
        <ul>
            <li><a href="/swagger/">Swagger Documentation</a></li>
            <li><a href="/api/token/">JWT Authentication</a></li>
            <li><a href="/admin/">Admin Panel</a></li>
        </ul>
    """
    )


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    # Debug Toolbar
    path("__debug__/", include("debug_toolbar.urls")),
    # API Documentation (drf-yasg)
    path("swagger.json", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Our API app
    path("api/", include("api.urls")),
]
