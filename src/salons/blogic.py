from django.db import models
from django.db.models import Q, Max, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from suppliers.models import SupplierCar
from promotions.models import PromotionSalon


def get_best_supplier_offer_for_salon(salon, car):
    supplier_offers = car.suppliercar_set.all()

    if not supplier_offers:
        return None

    best_offer = None
    now = timezone.now()

    salon_max_promo = PromotionSalon.objects.filter(
        Q(salon=salon)
        & Q(is_active=True)
        & Q(promotion__is_active=True)
        & Q(promotion__started_at__lte=now)
        & Q(promotion__ended_at__gte=now)
    ).aggregate(max_discount=Coalesce(Max("discount"), Value(Decimal("0.00"))))[
        "max_discount"
    ]

    for supplier_car in supplier_offers:
        base_price = Decimal(str(supplier_car.price))

        # Скидка поставщика (или 0)

        salon_promo_discount = Decimal(str(salon_max_promo or "0.00"))

        final_price = base_price * (1 - salon_promo_discount)

        offer = {
            "supplier_id": supplier_car.supplier.id,
            "supplier_name": supplier_car.supplier.name,
            "base_price": base_price,
            "salon_promo_discount": salon_promo_discount,
            "final_price": final_price,
        }

        if not best_offer or final_price < best_offer["final_price"]:
            best_offer = offer

    return best_offer


class SupplierChangeReason(models.TextChoices):
    INITIAL = "initial", "Initial supplier selection"
    PRICE = "price", "Better base price"
    PROMOTION = "promotion", "Better price due to promotion"


def determine_supplier_change_reason(salon, car, best_offer):
    """Определяем причину изменения поставщика"""

    active_suppliers = (
        SupplierCar.objects.filter(
            Q(car=car) & Q(is_active=True) & Q(supplier__is_active=True)
        )
        .select_related("supplier")
        .values("supplier__name", "price")
        .order_by("price")
    )

    if not active_suppliers.exists():
        return SupplierChangeReason.INITIAL

    min_price = None
    for supplier in active_suppliers:
        price = Decimal(str(supplier["price"]))
        if min_price is None or price < min_price:
            min_price = price

    if best_offer["final_price"] <= min_price:
        if best_offer["salon_promo_discount"] > Decimal("0.00"):
            return SupplierChangeReason.PROMOTION
        return SupplierChangeReason.PRICE
    return SupplierChangeReason.PRICE
