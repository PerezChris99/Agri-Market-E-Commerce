import re
import uuid

from django.conf import settings


class RequestIDMiddleware:
    """Attach a stable correlation ID to every request/response."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        candidate = (request.headers.get('X-Request-ID') or '')[:64]
        request.request_id = candidate if re.fullmatch(r'[A-Za-z0-9._-]{1,64}', candidate) else uuid.uuid4().hex
        if getattr(settings, 'SENTRY_DSN', ''):
            import sentry_sdk
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag('request_id', request.request_id)
        response = self.get_response(request)
        response['X-Request-ID'] = request.request_id
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(self)'
        return response
