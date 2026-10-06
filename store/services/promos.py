from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Customer, Order, PromoCode, PromoRedemption


def redeem_promo(*, promo_code, customer, order, order_total):
    """Atomically validate and redeem a promo code for one customer/order."""
    if isinstance(promo_code, PromoCode):
        promo_id = promo_code.pk
    else:
        promo_id = promo_code

    with transaction.atomic():
        promo = PromoCode.objects.select_for_update().get(pk=promo_id)
        locked_customer = Customer.objects.select_for_update().get(pk=customer.pk)
        locked_order = Order.objects.select_for_update().get(pk=order.pk)

        if locked_order.customer_id != locked_customer.pk:
            raise ValidationError('Promo redemption customer does not own this order.')
        if locked_order.complete:
            raise ValidationError('Completed orders cannot be assigned a promo code.')
        if PromoRedemption.objects.filter(order=locked_order).exists():
            raise ValidationError('This order already has a promo redemption.')

        valid, message = promo.is_valid(Decimal(str(order_total)), locked_customer)
        if not valid:
            raise ValidationError(message)

        discount = promo.calculate_discount(Decimal(str(order_total)))
        redemption = PromoRedemption.objects.create(
            promo=promo,
            customer=locked_customer,
            order=locked_order,
            discount_amount=discount,
        )
        promo.times_used += 1
        promo.save(update_fields=['times_used'])
        return redemption
