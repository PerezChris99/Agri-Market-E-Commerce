from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import uuid


class AdministrativeArea(models.Model):
    LEVELS = [("country", "Country"), ("region", "Region"), ("district", "District"), ("county", "County"), ("subcounty", "Subcounty"), ("parish", "Parish")]
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    level = models.CharField(max_length=20, choices=LEVELS)
    country_code = models.CharField(max_length=2, default="UG")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["level", "name"]
        indexes = [models.Index(fields=["level", "is_active", "name"], name="area_level_active_name_idx")]


class LogisticsHub(models.Model):
    TYPES = [("collection", "Collection Point"), ("warehouse", "Warehouse"), ("distribution", "Distribution Hub"), ("cold_chain", "Cold Chain Hub")]
    name = models.CharField(max_length=200)
    hub_type = models.CharField(max_length=20, choices=TYPES, default="collection")
    area = models.ForeignKey(AdministrativeArea, on_delete=models.PROTECT, null=True, blank=True, related_name="logistics_hubs")
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    capacity_units = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["area", "hub_type", "is_active"], name="hub_area_type_active_idx")]


class FarmerVerification(models.Model):
    STATUSES = [("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected"), ("suspended", "Suspended")]
    customer = models.OneToOneField("store.Customer", on_delete=models.CASCADE, related_name="farmer_verification")
    verification_type = models.CharField(max_length=40, default="identity")
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    reference_hash = models.CharField(max_length=128, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="farmer_verifications")
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def mark_verified(self, reviewer):
        self.status, self.verified_by, self.verified_at = "verified", reviewer, timezone.now()
        self.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])


class SupportTicket(models.Model):
    PRIORITIES = [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("critical", "Critical")]
    STATUSES = [("open", "Open"), ("assigned", "Assigned"), ("pending", "Pending"), ("resolved", "Resolved"), ("closed", "Closed")]
    ticket_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer = models.ForeignKey("store.Customer", on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets")
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITIES, default="normal")
    status = models.CharField(max_length=12, choices=STATUSES, default="open")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="support_tickets")
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["status", "priority", "-created_at"], name="ticket_status_priority_idx")]


class Incident(models.Model):
    SEVERITIES = [("sev1", "SEV-1"), ("sev2", "SEV-2"), ("sev3", "SEV-3"), ("sev4", "SEV-4")]
    STATUSES = [("open", "Open"), ("investigating", "Investigating"), ("mitigated", "Mitigated"), ("resolved", "Resolved")]
    incident_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    severity = models.CharField(max_length=5, choices=SEVERITIES, default="sev3")
    status = models.CharField(max_length=15, choices=STATUSES, default="open")
    title = models.CharField(max_length=200)
    description = models.TextField()
    started_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_incidents")
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["status", "severity", "-started_at"], name="incident_status_sev_idx")]


class SyncEvent(models.Model):
    STATUSES = [("accepted", "Accepted"), ("processed", "Processed"), ("rejected", "Rejected")]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sync_events")
    device_id = models.CharField(max_length=100)
    idempotency_key = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=60)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=12, choices=STATUSES, default="accepted")
    response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=["device_id", "-created_at"], name="sync_device_date_idx"), models.Index(fields=["status", "-created_at"], name="sync_status_date_idx")]


class ApiClient(models.Model):
    name = models.CharField(max_length=150)
    key_prefix = models.CharField(max_length=16)
    key_hash = models.CharField(max_length=64, unique=True)
    scopes = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_api_clients")
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        indexes = [models.Index(fields=["is_active", "expires_at"], name="api_client_active_expiry_idx")]
    def is_valid(self):
        return self.is_active and (self.expires_at is None or self.expires_at > timezone.now())
