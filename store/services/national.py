import hashlib
import hmac
import secrets

from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone

from ..models import Product
from ..national_models import AdministrativeArea, ApiClient, LogisticsHub, SyncEvent


def issue_api_key(*, name, created_by=None, scopes=None, expires_at=None):
    raw = "agr_" + secrets.token_urlsafe(32)
    client = ApiClient.objects.create(
        name=name,
        key_prefix=raw[:12],
        key_hash=hashlib.sha256(raw.encode()).hexdigest(),
        scopes=scopes or ["catalog:read"],
        created_by=created_by,
        expires_at=expires_at,
    )
    return client, raw


def authenticate_api_key(raw_key):
    if not raw_key:
        return None
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    client = ApiClient.objects.filter(key_hash=digest).first()
    if not client or not client.is_valid():
        return None
    if not hmac.compare_digest(client.key_hash, digest):
        return None
    ApiClient.objects.filter(pk=client.pk).update(last_used_at=timezone.now())
    return client


@transaction.atomic
def accept_sync_event(*, api_client, device_id, idempotency_key, event_type, payload, user=None):
    if not api_client or not api_client.is_valid():
        raise ValueError("A valid API client is required.")
    if not device_id or len(device_id) > 100:
        raise ValueError("A valid device_id is required.")
    if not idempotency_key or len(idempotency_key) > 128:
        raise ValueError("A valid idempotency_key is required.")
    if not event_type or len(event_type) > 60:
        raise ValueError("A valid event_type is required.")
    existing = SyncEvent.objects.select_for_update().filter(idempotency_key=idempotency_key).first()
    if existing:
        return existing, False
    event = SyncEvent.objects.create(
        user=user, device_id=device_id, idempotency_key=idempotency_key,
        event_type=event_type, payload=payload or {},
        response={"accepted": True, "idempotency_key": idempotency_key},
    )
    return event, True


def catalog_page(*, page=1, page_size=50):
    page = max(int(page or 1), 1)
    page_size = min(max(int(page_size or 50), 1), 100)
    return Paginator(
        Product.objects.filter(is_active=True)
        .select_related("category")
        .only("id", "slug", "name", "price", "unit", "stock", "category__name")
        .order_by("id"),
        page_size,
    ).get_page(page)


def area_tree():
    return list(AdministrativeArea.objects.filter(is_active=True).values(
        "id", "name", "code", "level", "parent_id"
    ).order_by("level", "name"))


def nearest_hubs(*, limit=10):
    limit = min(max(int(limit or 10), 1), 50)
    return list(
        LogisticsHub.objects.filter(is_active=True).select_related("area")
        .values("id", "name", "hub_type", "area__name", "latitude", "longitude", "capacity_units")
        .order_by("name")[:limit]
    )


def readiness_snapshot():
    from django.conf import settings
    from django.db import connection

    checks = {}
    try:
        connection.ensure_connection()
        checks["database"] = True
    except Exception:
        checks["database"] = False
    checks["redis_configured"] = bool(getattr(settings, "REDIS_URL", ""))
    checks["object_storage_configured"] = bool(getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""))
    checks["payment_webhook_secret"] = bool(getattr(settings, "MOMO_WEBHOOK_SECRET", ""))
    checks["debug_disabled"] = not settings.DEBUG
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "version": getattr(settings, "APP_VERSION", "unknown"),
    }
