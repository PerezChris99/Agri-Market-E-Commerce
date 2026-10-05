from django.db import transaction

from ..models import Order, ShippingAddress
from .audit import record_event


def finalize_order(*, order_id, payment_method, transaction_id='', payment=None, customer=None, shipping=None, actor=None, ip_address=None):
    """Finalize a verified order inside one database transaction."""
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.complete:
            return None

        if payment_method == 'cod':
            order.place_cash_on_delivery()
        elif payment_method in {'mtn', 'airtel'}:
            if payment is None:
                raise ValueError('Verified mobile-money payment is required.')
            order.mark_as_paid(payment.transaction_id, payment_method=f'mobile_money_{payment.provider}')
        elif payment_method == 'paypal':
            order.mark_as_paid(transaction_id, payment_method='paypal')
        else:
            raise ValueError('Unsupported payment method.')

        if shipping:
            ShippingAddress.objects.update_or_create(
                order=order,
                defaults={
                    'customer': customer,
                    'full_name': shipping['name'],
                    'phone': shipping['phone'],
                    'address': shipping['address'],
                    'city': shipping['city'],
                    'district': shipping['region'],
                    'region': shipping['region'],
                    'country': shipping['country'],
                    'postal_code': shipping['postal_code'],
                    'landmark': shipping.get('landmark', '')[:200],
                    'delivery_notes': shipping.get('delivery_notes', ''),
                },
            )

        record_event(
            action='order.completed',
            object_type='Order',
            object_id=order.order_id,
            actor=actor,
            metadata={'payment_method': payment_method, 'amount': str(order.get_cart_total)},
            ip_address=ip_address,
        )
        return order
