from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .services.national import catalog_page, area_tree, nearest_hubs, readiness_snapshot, authenticate_api_key

def key_required(view):
    def wrapped(request, *args, **kwargs):
        client = authenticate_api_key(request.headers.get("X-API-Key", ""))
        if not client:
            return JsonResponse({"error": "invalid_api_key"}, status=401)
        request.api_client = client
        return view(request, *args, **kwargs)
    return wrapped

@require_GET
def products(request):
    page = catalog_page(page=request.GET.get("page", 1), page_size=request.GET.get("page_size", 50))
    return JsonResponse({"version": "v1", "count": page.paginator.count, "page": page.number, "pages": page.paginator.num_pages, "results": [{"id": p.id, "slug": p.slug, "name": p.name, "price": str(p.price), "unit": p.unit, "stock": p.stock, "category": p.category.name if p.category_id else None} for p in page.object_list]})

@require_GET
def areas(request):
    return JsonResponse({"version": "v1", "results": area_tree()})

@require_GET
def hubs(request):
    return JsonResponse({"version": "v1", "results": nearest_hubs(limit=request.GET.get("limit", 10))})

@require_POST
@key_required
def sync(request):
    import json
    try:
        data = json.loads(request.body or "{}")
        event, created = accept_sync_event(
            api_client=request.api_client,
            device_id=data.get("device_id", ""),
            idempotency_key=data.get("idempotency_key", ""),
            event_type=data.get("event_type", ""),
            payload=data.get("payload") or {},
            user=request.user if request.user.is_authenticated else None,
        )
    except (ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"version":"v1","accepted":True,"created":created,"idempotency_key":event.idempotency_key,"status":event.status})

@require_GET
@key_required
def readiness(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"error": "staff_required"}, status=403)
    snapshot = readiness_snapshot()
    return JsonResponse(snapshot, status=200 if snapshot["ready"] else 503)
