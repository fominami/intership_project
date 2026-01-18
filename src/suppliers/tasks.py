from celery import shared_task
from django.db.models import Max, F, Sum
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from salons.models import Salon
from salons.models import SalonCar
from cars.models import Car
from suppliers.models import SupplierCar
from promotions.models import PromotionSalon
import logging

logger = logging.getLogger(__name__)


@shared_task
def analyze_demand_and_buy():
    logger.info("=== STARTING DEMAND ANALYSIS ===")

    active_salons = Salon.objects.filter(is_active=True).select_related("user")
    logger.info(f"Salons found: {active_salons.count()}")

    total_purchases = 0
    total_cost = Decimal("0.00")

    for salon in active_salons:
        logger.info(f"\nSALON: {salon.name}")

        models_to_buy = get_models_to_buy(salon)

        if not models_to_buy:
            logger.info("No cars to purchase")
            continue

        for car, needed_qty in models_to_buy.items():
            logger.info(f" {car}: need {needed_qty} units")

            best_offer = get_best_supplier_offer(salon, car, needed_qty)
            if not best_offer:
                log_no_purchase(car, needed_qty, "no suppliers available")
                continue

            if not check_salon_balance(salon, best_offer["total_cost"]):
                log_no_purchase(car, needed_qty, "insufficient balance")
                continue

            try:
                transaction_data = create_purchase_transaction(salon, best_offer)
                log_purchase_success(salon, transaction_data)
                total_purchases += 1
                total_cost += best_offer["total_cost"]
            except Exception as e:
                logger.error(f"Error: {e}")
                continue

    logger.info(f"\nRESULT: {total_purchases} purchases for ${total_cost:.0f}")
    return f"Purchases: {total_purchases}, Total: ${total_cost:.0f}"


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


def log_no_purchase(car, quantity, reason):
    logger.warning(f"Did not buy {car}: x{quantity} — {reason}")


@transaction.atomic
def create_purchase_transaction(salon, best_offer):
    car = best_offer["supplier_car"].car
    quantity = best_offer["quantity"]
    total_cost = best_offer["total_cost"]

    salon_car = SalonCar.objects.get(salon=salon, car=car)
    salon_car.count = F("count") + quantity
    salon_car.save()
    salon_car.refresh_from_db()

    salon.balance = F("balance") - total_cost
    salon.save()
    salon.refresh_from_db()

    logger.info(f" SalonCar: {salon_car.car} count={salon_car.count}")
    logger.info(f" Salon balance: ${salon.balance}")

    return {
        "salon": salon,
        "supplier": best_offer["supplier"],
        "car": car,
        "quantity": quantity,
        "unit_price": best_offer["final_price"],
        "total_cost": total_cost,
        "reason": "stock depleted",
    }


def log_purchase_success(salon, transaction_data):
    """Log successful purchase"""
    logger.info(
        f"PURCHASED: {salon.name} ← {transaction_data['supplier'].name}: {transaction_data['car']} x{transaction_data['quantity']} for ${transaction_data['total_cost']:.0f}"
    )
