from celery import shared_task
from django.db import models
from django.db.models import Q, Prefetch, Max, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
import logging
from salons.models import Salon
from cars.models import Car
from suppliers.models import SupplierCar
from promotions.models import PromotionSalon

logger = logging.getLogger(__name__)


@shared_task
def update_best_suppliers_for_salons():
    logger.info("=== Checking active suppliers ===")

    # Получаем активные салоны
    active_salons = (
        Salon.objects.filter(Q(is_active=True))
        .prefetch_related(
            Prefetch(
                "cars",
                queryset=Car.objects.filter(is_active=True)
                .prefetch_related(
                    Prefetch(
                        "suppliercar_set",
                        queryset=SupplierCar.objects.filter(is_active=True)
                        .select_related("supplier")
                        .only("id", "supplier_id", "car_id", "price", "is_active"),
                    )
                )
                .only("id", "brand", "model", "is_active"),
            )
        )
        .only("id", "name", "balance", "is_active", "user_id")
    )

    logger.info(f"Active salons: {active_salons.count()}")

    total_updates = 0
    total_changes = 0
    best_suppliers_data = []

    for salon in active_salons:
        logger.info(f"\nSalon: {salon.name} (ID: {salon.id})")

        # Алализ цен для каждого автомобиля
        salon_cars = salon.cars.all()

        if not salon_cars:
            logger.info("No active cars")
            continue

        for car in salon_cars:
            # Поиск лучшего поставщика
            best_offer = get_best_supplier_offer_for_salon(salon, car)

            if not best_offer:
                logger.warning(f" {car.brand} {car.model}: no active suppliers")
                continue

            # Определяем причину изменения
            reason = determine_supplier_change_reason(salon, car, best_offer)

            # Логирование
            log_supplier_update(salon, car, best_offer, reason)
            best_suppliers_data.append(
                {
                    "salon_id": str(salon.id),
                    "car_id": str(car.id),
                    "supplier_id": str(best_offer["supplier_id"]),
                    "final_price": float(best_offer["final_price"]),
                    "reason": reason,
                    "checked_at": timezone.now().isoformat(),
                }
            )

            total_changes += 1
            total_updates += 1

    logger.info(f"\nResult: checked {total_updates} models, active {total_changes}")
    return {
        "checked": total_updates,
        "updated": total_changes,
        "data": best_suppliers_data,
    }


def get_best_supplier_offer_for_salon(salon, car):
    """Получаем лучшее предложение + актуальные скидки"""

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


def log_supplier_update(salon, car, best_offer, reason):
    logger.info(f"   {car.brand} {car.model}:")
    logger.info(f"     Supplier: {best_offer['supplier_name']}")
    logger.info(
        f"     Price: ${best_offer['base_price']:.2f} → ${best_offer['final_price']:.2f}"
    )
    logger.info(
        f"     Salon's promotion: {best_offer['salon_promo_discount'] * 100:.1f}%"
    )
    logger.info(f"     Reason: {reason.label}")
