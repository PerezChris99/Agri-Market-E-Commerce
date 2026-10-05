from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Delivery, DeliveryLocation

ALLOWED_STATUSES = {status for status, _ in Delivery.STATUS_CHOICES}


def update_location(*, delivery, latitude, longitude, accuracy=None, actor=None):
    if actor is not None and not actor.is_staff:
        rider = delivery.rider
        if not rider or rider.user_id != actor.id:
            raise PermissionError('Only the assigned rider or staff may update delivery location.')
    lat = Decimal(str(latitude))
    lng = Decimal(str(longitude))
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValidationError('Invalid GPS coordinates.')
    with transaction.atomic():
        DeliveryLocation.objects.create(
            delivery=delivery,
            latitude=lat,
            longitude=lng,
            accuracy=accuracy,
        )
        delivery.current_lat = lat
        delivery.current_lng = lng
        delivery.save(update_fields=['current_lat', 'current_lng', 'updated_at'])
    return delivery


def update_status(*, delivery, new_status, notes='', actor=None):
    if new_status not in ALLOWED_STATUSES:
        raise ValidationError('Invalid delivery status.')
    if actor is not None and not actor.is_staff:
        rider = delivery.rider
        if not rider or rider.user_id != actor.id:
            raise PermissionError('Only the assigned rider or staff may update delivery status.')
    if delivery.status == 'delivered' and new_status != 'delivered':
        raise ValidationError('Delivered deliveries cannot move backwards.')
    delivery.update_status(new_status, notes=notes)
    return delivery
