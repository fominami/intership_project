from django.db.models import Q, Prefetch, Count
from django.utils import timezone
from decimal import Decimal
import logging
from salons.models import Salon
from promotions.models import PromotionSalon
from suppliers.models import SupplierCar

logger = logging.getLogger(__name__)


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
