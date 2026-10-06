from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Customer, Product
from .national_models import AdministrativeArea, SyncEvent
from .services.national import issue_api_key, authenticate_api_key, accept_sync_event


class NationalQualityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quality-user")
        self.customer = Customer.objects.get(user=self.user)
        Product.objects.create(name="Matooke", price="5000.00", stock=10)

    def test_api_secret_is_hashed(self):
        client, raw = issue_api_key(name="quality")
        self.assertNotEqual(client.key_hash, raw)
        self.assertEqual(authenticate_api_key(raw).pk, client.pk)

    def test_sync_is_idempotent(self):
        client, _ = issue_api_key(name="sync")
        first, created = accept_sync_event(api_client=client, device_id="d1", idempotency_key="k1", event_type="catalog.refresh", payload={})
        second, duplicate = accept_sync_event(api_client=client, device_id="d1", idempotency_key="k1", event_type="catalog.refresh", payload={"changed": True})
        self.assertTrue(created)
        self.assertFalse(duplicate)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SyncEvent.objects.count(), 1)

    def test_area_api_is_available(self):
        AdministrativeArea.objects.create(name="Central", code="UG-C", level="region")
        response = self.client.get(reverse("api_v1_areas"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["code"], "UG-C")

    def test_sync_api_rejects_missing_key(self):
        response = self.client.post(reverse("api_v1_sync"), data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_expired_key_is_rejected(self):
        from django.utils import timezone
        client, raw = issue_api_key(name="expired", expires_at=timezone.now() - timezone.timedelta(minutes=1))
        self.assertFalse(client.is_valid())
        self.assertIsNone(authenticate_api_key(raw))

    def test_disabled_key_is_rejected(self):
        client, raw = issue_api_key(name="disabled")
        client.is_active = False
        client.save(update_fields=["is_active"])
        self.assertIsNone(authenticate_api_key(raw))

    def test_hub_api_is_available(self):
        from .national_models import LogisticsHub
        LogisticsHub.objects.create(name="Central Hub", hub_type="collection")
        response = self.client.get(reverse("api_v1_hubs"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["name"], "Central Hub")

    def test_readiness_is_staff_protected(self):
        client, raw = issue_api_key(name="readiness")
        response = self.client.get(reverse("api_v1_readiness"), HTTP_X_API_KEY=raw)
        self.assertEqual(response.status_code, 403)

