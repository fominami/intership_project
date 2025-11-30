from django.urls import path, include
from rest_framework.routers import DefaultRouter
from deals.views import DealViewSet

router = DefaultRouter()
router.register("", DealViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
