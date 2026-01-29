from celery import shared_task
from django.db.models import Q, Prefetch
from django.utils import timezone
import logging
from salons.models import Salon
from cars.models import Car
from suppliers.models import SupplierCar
from salons.blogic import (
    determine_supplier_change_reason,
    get_best_supplier_offer_for_salon,
)

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

            logger.info(
                f"{car.brand} {car.model}:\n"
                f"  Supplier: {best_offer['supplier_name']}\n"
                f"  Price: ${best_offer['base_price']:.2f} → ${best_offer['final_price']:.2f}\n"
                f"  Salon's promotion: {best_offer['salon_promo_discount'] * 100:.1f}%\n"
                f"  Reason: {reason.label}"
            )
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
