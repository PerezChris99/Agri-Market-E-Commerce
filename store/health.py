import os
import time
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

def _response(payload, status=200):
    response = JsonResponse(payload, status=status)
    response['Cache-Control'] = 'no-store, max-age=0'
    return response

def live(request):
    return _response({'status': 'ok', 'service': 'agrimarket'})

def ready(request):
    checks = {}
    started = time.monotonic()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        checks['database'] = 'ok'
    except Exception:
        checks['database'] = 'failed'
    try:
        key = 'health:ready'
        cache.set(key, 'ok', 5)
        checks['cache'] = 'ok' if cache.get(key) == 'ok' else 'failed'
    except Exception:
        checks['cache'] = 'failed'
    healthy = all(value == 'ok' for value in checks.values())
    return _response({'status': 'ok' if healthy else 'degraded', 'service': 'agrimarket', 'version': os.environ.get('APP_VERSION', 'unknown'), 'checks': checks, 'duration_ms': round((time.monotonic() - started) * 1000, 2)}, 200 if healthy else 503)
