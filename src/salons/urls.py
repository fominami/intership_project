from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalonViewSet, SalonCarViewSet

router = DefaultRouter()
router.register("salons", SalonViewSet)
router.register(
    "salons/(?P<salon_pk>[^/.]+)/cars", SalonCarViewSet, basename="salon-cars"
)

urlpatterns = [
    path("", include(router.urls)),
]
