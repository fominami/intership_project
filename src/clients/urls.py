from django.urls import path, include
from rest_framework.routers import DefaultRouter
from clients.views import ClientViewSet

router = DefaultRouter()
router.register("client", ClientViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
