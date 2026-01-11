from django.urls import path, include
from rest_framework.routers import DefaultRouter
from suppliers.views import SupplierViewSet, SupplierCarViewSet

router = DefaultRouter()
router.register("suppliers", SupplierViewSet)
router.register(
    "suppliers/(?P<salon_pk>[^/.]+)/cars", SupplierCarViewSet, basename="supplier-cars"
)

urlpatterns = [
    path("", include(router.urls)),
]
