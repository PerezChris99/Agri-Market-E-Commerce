from decimal import Decimal

from django.db.models import Q

from ..models import MobileMoneyPayment, Order
from ..payments import verify_paypal_transaction


def get_verified_mobile_payment(*, order, transaction_id, provider, amount):
    """Return a matching successful mobile payment or None."""
    return MobileMoneyPayment.objects.filter(
        order=order,
        status='successful',
        provider=provider,
        amount=Decimal(str(amount)),
    ).filter(
        Q(provider_reference=transaction_id)
        | Q(external_reference=transaction_id)
        | Q(transaction_id=transaction_id)
    ).first()


def verify_paypal(*, transaction_id, amount):
    return bool(transaction_id and verify_paypal_transaction(transaction_id, Decimal(str(amount))))


def complete_verified_payment(*, order, payment, transaction_id=None):
    """Finalize an already verified payment through the order transaction boundary."""
    transaction = transaction_id or payment.transaction_id
    return order.mark_as_paid(transaction, payment_method=f'mobile_money_{payment.provider}')
