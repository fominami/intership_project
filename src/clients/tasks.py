from celery import shared_task
from django.db.models import F, Q
import logging
from django.db import transaction
from clients.models import Client
from salons.models import SalonCar, BestSupplierForSalon
from deals.models import Deal
from clients.blogic import (
    check_client_eligible,
    get_client_preferred_cars,
    find_suitable_salons,
    select_best_salon,
)


logger = logging.getLogger(__name__)


@shared_task
def process_pending_deals():
    logger.info("=== Deal processing ===")

    active_clients = (
        Client.objects.filter(
            Q(is_active=True)
            & Q(user__is_active=True)
            & Q(user__is_email_verified=True)
        )
        .select_related("user")
        .prefetch_related("preferences")
    )

    logger.info(f"Active clients: {active_clients.count()}")

    total_processed = 0
    total_successful = 0

    for client in active_clients:
        if not check_client_eligible(client):
            logger.warning(
                f"Client `{client.user.username}` is not eligible: validation checks failed"
            )
            continue

        logger.info(f"\nClient: {client.user.username} (ID: {client.id})")
        logger.info(f"Balance: ${client.balance:.2f}")

        preferred_cars = get_client_preferred_cars(client)

        if not preferred_cars:
            logger.info("No preference")
            continue

        for car_id, max_price in preferred_cars:
            logger.info(f"\n  Found: Car ID {car_id}, max price: ${max_price:.2f}")

            suitable_salons = find_suitable_salons(car_id, max_price)

            if not suitable_salons:
                logger.warning("there are no suitable salons")
                continue

            chosen_salon = select_best_salon(client, suitable_salons)

            if not chosen_salon:
                continue

            deal = process_deal(client, chosen_salon)

            if deal:
                logger.info(
                    "Successful completed:\n"
                    f"Client: {client.user.username}\n"
                    f"Salon: {chosen_salon.name}\n"
                    f"Car: {deal.car.brand} {deal.car.model}\n"
                    f"Supplier: {deal.supplier.name}\n"
                    f"Sum: ${deal.sum:.2f}\n"
                    f"Deal id: {deal.id}\n"
                    f"Client balance: ${client.balance:.2f}\n"
                    f"Salon balance: ${chosen_salon.balance:.2f}"
                )
                total_successful += 1

            total_processed += 1

    logger.info(f"\nResult: processed {total_processed}, successful {total_successful}")
    return {"processed": total_processed, "successful": total_successful}


@transaction.atomic
def process_deal(client, salon):
    try:
        best_supplier = (
            BestSupplierForSalon.objects.filter(Q(salon=salon) & Q(is_active=True))
            .select_related("supplier")
            .first()
        )

        if not best_supplier:
            logger.error(f"No best supplier {salon.name}")
            return None

        car = best_supplier.car
        final_price = best_supplier.final_price

        # Сheck client's balance
        if client.balance < final_price:
            logger.warning(
                f" Small balance: ${client.balance:.2f} < ${final_price:.2f}"
            )
            return None

        # reduce client's balance
        client.balance = F("balance") - final_price
        client.save()
        client.refresh_from_db()

        # reduce count in salon
        salon_car = SalonCar.objects.get(salon=salon, car=car)
        salon_car.count = F("count") - 1
        salon_car.save()

        # increasing the salon balance
        salon.balance = F("balance") + final_price
        salon.save()
        salon.refresh_from_db()

        # Create Deal
        deal = Deal.objects.create(
            salon=salon,
            car=car,
            supplier=best_supplier.supplier,
            client=client,
            sum=final_price,
        )

        logger.info(f"Deal was created: ID {deal.id}, sum ${final_price:.2f}")

        return deal

    except Exception as e:
        logger.error(f" Error in deal: {str(e)}")
        return None
