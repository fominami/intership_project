from celery import shared_task
from django.db.models import F, Q, Prefetch, Count
from django.utils import timezone
from decimal import Decimal
import logging
from django.db import transaction
from clients.models import Client
from salons.models import Salon
from promotions.models import PromotionSalon
from suppliers.models import SupplierCar
from salons.models import SalonCar, BestSupplierForSalon
from deals.models import Deal

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
                log_deal_success(client, chosen_salon, deal)
                total_successful += 1

            total_processed += 1

    logger.info(f"\nResult: processed {total_processed}, successful {total_successful}")
    return {"processed": total_processed, "successful": total_successful}


def check_client_eligible(client):
    if client.balance <= Decimal("0.00"):
        logger.warning(f"Balance is empty: ${client.balance:.2f}")
        return False

    return True


def get_client_preferred_cars(client):
    preferences = client.preferences.filter(
        Q(is_active=True) & Q(category="preferred_car")
    )

    preferred_cars = []

    for pref in preferences:
        try:
            car_id, max_price = pref.value.split(":")
            max_price = Decimal(max_price)
            preferred_cars.append((car_id, max_price))
        except ValueError:
            logger.warning(f"Problems with preference: {pref.value}")
            continue

    return preferred_cars


def find_suitable_salons(car_id, max_price):
    suitable_salons = (
        Salon.objects.filter(
            Q(is_active=True) & Q(saloncar__car_id=car_id) & Q(saloncar__count__gt=0)
        )
        .distinct()
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "best_suppliers",
                queryset=SupplierCar.objects.filter(
                    Q(is_active=True) & Q(car_id=car_id)
                ).select_related("supplier"),
            ),
            Prefetch(
                "salon_promotions",
                queryset=PromotionSalon.objects.filter(
                    Q(is_active=True)
                    & Q(promotion__is_active=True)
                    & Q(promotion__started_at__lte=timezone.now())
                    & Q(promotion__ended_at__gte=timezone.now())
                ).select_related("promotion"),
            ),
            "deals",
        )
        .annotate(
            successful_sales_count=Count("deals", filter=Q(deals__is_active=True))
        )
        .values_list(
            "id",
            "name",
            "best_suppliers__final_price",
            "successful_sales_count",
            "salon_promotions__discount",
            flat=False,
        )
    )

    results = []

    for (
        salon_id,
        salon_name,
        final_price,
        sales_count,
        promo_discount,
    ) in suitable_salons:
        if final_price is None:
            continue

        final_price = Decimal(str(final_price))

        if final_price > max_price:
            continue

        results.append(
            {
                "salon_id": salon_id,
                "salon_name": salon_name,
                "price": final_price,
                "successful_sales": sales_count or 0,
                "has_promotion": promo_discount is not None,
                "promo_discount": Decimal(str(promo_discount or "0.00")),
            }
        )

    return results


def select_best_salon(client, suitable_salons):
    if not suitable_salons:
        return None

    def salon_sort_key(salon):
        return (salon["price"], not salon["has_promotion"], -salon["successful_sales"])

    sorted_salons = sorted(suitable_salons, key=salon_sort_key)
    best_salon_data = sorted_salons[0]

    salon = (
        Salon.objects.filter(id=best_salon_data["salon_id"])
        .select_related("user")
        .first()
    )

    logger.info(f"Salon: {best_salon_data['salon_name']}")
    logger.info(f"Price: ${best_salon_data['price']:.2f}")
    logger.info(f"Promotion: {'Yes' if best_salon_data['has_promotion'] else 'No'}")
    logger.info(f"Successful sales: {best_salon_data['successful_sales']}")

    return salon


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

        # Проверка баланса клиента
        if client.balance < final_price:
            logger.warning(
                f" Small balance: ${client.balance:.2f} < ${final_price:.2f}"
            )
            return None

        # Уменьшаем баланс клиента
        client.balance = F("balance") - final_price
        client.save()
        client.refresh_from_db()

        # Уменьшаем количество в салоне
        salon_car = SalonCar.objects.get(salon=salon, car=car)
        salon_car.count = F("count") - 1
        salon_car.save()

        # Увеличиваем баланс салона
        salon.balance = F("balance") + final_price
        salon.save()
        salon.refresh_from_db()

        # Создаем Deal
        deal = Deal.objects.create(
            salon=salon,
            car=car,
            supplier=best_supplier.supplier,
            client=client,
            sum=final_price,
        )

        logger.info(f"Deal was created: ID {deal.id}, сумма ${final_price:.2f}")

        return deal

    except Exception as e:
        logger.error(f" Errir in deal: {str(e)}")
        return None


def log_deal_success(client, salon, deal):
    logger.info("Successful complited:")
    logger.info(f" Client: {client.user.username}")
    logger.info(f"Salon: {salon.name}")
    logger.info(f"Car: {deal.car.brand} {deal.car.model}")
    logger.info(f"Supplier: {deal.supplier.name}")
    logger.info(f"Sum: ${deal.sum:.2f}")
    logger.info(f"deal's id: {deal.id}")
    logger.info(f"client's balance : ${client.balance:.2f}")
    logger.info(f"salon's balance: ${salon.balance:.2f}")
