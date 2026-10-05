from django.utils import timezone

from ..models import AuditLog


def record_event(*, action, object_type, object_id='', actor=None, metadata=None, ip_address=None):
    """Record a security/operational event without exposing sensitive payloads."""
    safe_metadata = metadata or {}
    return AuditLog.objects.create(
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        actor=actor,
        metadata=safe_metadata,
        ip_address=ip_address,
    )
