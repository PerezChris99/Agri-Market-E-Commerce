from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("store","0015_sync_event")]
    operations=[migrations.CreateModel(
        name="ApiClient",
        fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("name",models.CharField(max_length=150)),
            ("key_prefix",models.CharField(max_length=16)),
            ("key_hash",models.CharField(max_length=64,unique=True)),
            ("scopes",models.JSONField(default=list,blank=True)),
            ("is_active",models.BooleanField(default=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("last_used_at",models.DateTimeField(null=True,blank=True)),
            ("expires_at",models.DateTimeField(null=True,blank=True)),
            ("created_by",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,related_name="created_api_clients",to="auth.user")),
        ],
        options={"indexes":[models.Index(fields=["is_active","expires_at"],name="api_client_active_expiry_idx")]},
    )]
