import logging

from celery import shared_task
from django.db import close_old_connections

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def send_order_sms_task(self, order_id, notification_type='payment_received'):
    """Send an order SMS outside the HTTP request lifecycle."""
    from .models import Order
    from .sms import send_order_sms

    close_old_connections()
    order = Order.objects.get(pk=order_id)
    result = send_order_sms(order, notification_type)
    logger.info('Order SMS task completed for order=%s type=%s result=%s', order.order_id, notification_type, result[0])
    return {'success': result[0], 'message_id': result[1]}
