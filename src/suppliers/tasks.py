from celery import shared_task
from django.db.models import F
from django.db import transaction
from decimal import Decimal
from salons.models import Salon
from salons.models import SalonCar
import logging
from suppliers.blogic import (
    get_models_to_buy,
    get_best_supplier_offer,
    check_salon_balance,
)

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
                logger.info(
                    f"PURCHASED: {salon.name} ← {transaction_data['supplier'].name}: {transaction_data['car']} x{transaction_data['quantity']} for ${transaction_data['total_cost']:.0f}"
                )
                total_purchases += 1
                total_cost += best_offer["total_cost"]
            except Exception as e:
                logger.error(f"Error: {e}")
                continue

    logger.info(f"\nRESULT: {total_purchases} purchases for ${total_cost:.0f}")
    return f"Purchases: {total_purchases}, Total: ${total_cost:.0f}"


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

    logger.info(
        f" SalonCar: {salon_car.car} count={salon_car.count}\n"
        f" Salon balance: ${salon.balance}"
    )

    return {
        "salon": salon,
        "supplier": best_offer["supplier"],
        "car": car,
        "quantity": quantity,
        "unit_price": best_offer["final_price"],
        "total_cost": total_cost,
        "reason": "stock depleted",
    }


def log_no_purchase(car, quantity, reason):
    logger.warning(f"Did not buy {car}: x{quantity} — {reason}")
