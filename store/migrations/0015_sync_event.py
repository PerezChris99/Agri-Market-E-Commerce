from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("store","0014_incident")]
    operations=[migrations.CreateModel(
        name="SyncEvent",
        fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("device_id",models.CharField(max_length=100)),
            ("idempotency_key",models.CharField(max_length=128,unique=True)),
            ("event_type",models.CharField(max_length=60)),
            ("payload",models.JSONField(default=dict)),
            ("status",models.CharField(max_length=12,default="accepted",choices=[("accepted","Accepted"),("processed","Processed"),("rejected","Rejected")])),
            ("response",models.JSONField(default=dict,blank=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("processed_at",models.DateTimeField(null=True,blank=True)),
            ("user",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,related_name="sync_events",to="auth.user")),
        ],
        options={"indexes":[models.Index(fields=["device_id","-created_at"],name="sync_device_date_idx"),models.Index(fields=["status","-created_at"],name="sync_status_date_idx")]},
    )]
