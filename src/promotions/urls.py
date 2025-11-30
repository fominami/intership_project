from django.urls import path, include
from rest_framework.routers import DefaultRouter
from promotions.views import (
    PromotionViewSet,
    PromotionSalonViewSet,
    PromotionCarViewSet,
)

router = DefaultRouter()
router.register("promotions", PromotionViewSet)
router.register(
    "promotions/(?P<promotion_pk>[^/.]+)/salon",
    PromotionSalonViewSet,
    basename="promotion-salons",
)
router.register(
    "promotions/(?P<promotion_pk>[^/.]+)/Car",
    PromotionCarViewSet,
    basename="promotion-cars",
)
urlpatterns = [
    path("", include(router.urls)),
]
