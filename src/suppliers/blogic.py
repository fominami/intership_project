from django.db.models import Max, Sum
from decimal import Decimal
from django.utils import timezone
from salons.models import SalonCar
from cars.models import Car
from suppliers.models import SupplierCar
from promotions.models import PromotionSalon
import logging

logger = logging.getLogger(__name__)


def get_models_to_buy(salon):
    models_to_buy = {}

    salon_cars = (
        SalonCar.objects.filter(salon=salon).values_list("car_id", flat=True).distinct()
    )

    for car_id in salon_cars:
        car_model = Car.objects.get(id=car_id)

        total_count = (
            SalonCar.objects.filter(salon=salon, car_id=car_id).aggregate(
                total=Sum("count")
            )["total"]
            or 0
        )

        logger.info(f"{car_model}: total {total_count}")

        if total_count > 0:
            target_ratio = 0.7
            target_count = int(total_count * target_ratio)
            current_entry = SalonCar.objects.get(salon=salon, car_id=car_id)
            current_count = current_entry.count

            if current_count < target_count:
                needed_qty = target_count - current_count
                models_to_buy[car_model] = needed_qty
                logger.info(f"  🛒 {car_model}: need to buy {needed_qty} units")

    return models_to_buy


def get_best_supplier_offer(salon, car, quantity):
    supplier_offers = SupplierCar.objects.filter(
        car_id=car.id, is_active=True
    ).select_related("supplier")

    if not supplier_offers.exists():
        return None

    best_offer = None
    now = timezone.now()

    salon_promo_discount = PromotionSalon.objects.filter(
        salon=salon,
        is_active=True,
        promotion__is_active=True,
        promotion__started_at__lte=now,
        promotion__ended_at__gte=now,
    ).aggregate(max_discount=Max("discount"))["max_discount"] or Decimal("0.00")

    for supplier_car in supplier_offers:
        base_price = Decimal(str(supplier_car.price))
        supplier_discount = Decimal(str(supplier_car.supplier.discount or "0.00"))
        price_after_supplier = base_price * (1 - supplier_discount)
        final_price = price_after_supplier * (1 - salon_promo_discount)
        total_cost = final_price * quantity

        offer = {
            "supplier_car": supplier_car,
            "supplier": supplier_car.supplier,
            "base_price": base_price,
            "supplier_discount": supplier_discount,
            "salon_promo_discount": salon_promo_discount,
            "final_price": final_price,
            "quantity": quantity,
            "total_cost": total_cost,
        }

        if not best_offer or total_cost < best_offer["total_cost"]:
            best_offer = offer

    if best_offer:
        logger.info(
            f" {best_offer['supplier'].name}: ${best_offer['base_price']:.0f} → ${best_offer['final_price']:.0f}/unit"
        )

    return best_offer


def check_salon_balance(salon, total_cost):
    return salon.balance >= total_cost
