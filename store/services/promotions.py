from decimal import Decimal

from django.db import transaction

from ..models import Customer, Order, PromoCode, PromoRedemption


def redeem_promo(promo, customer, order, order_total):
    """Atomically validate and redeem a promo code exactly once for an order."""
    if not isinstance(customer, Customer):
        customer = customer.customer

    with transaction.atomic():
        locked_promo = PromoCode.objects.select_for_update().get(pk=promo.pk)
        valid, message = locked_promo.is_valid(order_total, customer)
        if not valid:
            raise ValueError(message)

        if PromoRedemption.objects.filter(order=order).exists():
            raise ValueError('This order already has a promo code redemption.')

        discount = Decimal(str(locked_promo.calculate_discount(order_total)))
        redemption = PromoRedemption.objects.create(
            promo=locked_promo,
            customer=customer,
            order=order,
            discount_amount=discount,
        )
        locked_promo.times_used += 1
        locked_promo.save(update_fields=['times_used'])
        return redemption
