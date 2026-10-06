from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid

class Migration(migrations.Migration):
    dependencies=[("store","0013_support_ticket")]
    operations=[migrations.CreateModel(
        name="Incident",
        fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("incident_id",models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
            ("severity",models.CharField(max_length=5,default="sev3",choices=[("sev1","SEV-1"),("sev2","SEV-2"),("sev3","SEV-3"),("sev4","SEV-4")])),
            ("status",models.CharField(max_length=15,default="open",choices=[("open","Open"),("investigating","Investigating"),("mitigated","Mitigated"),("resolved","Resolved")])),
            ("title",models.CharField(max_length=200)),
            ("description",models.TextField()),
            ("started_at",models.DateTimeField(default=django.utils.timezone.now)),
            ("resolved_at",models.DateTimeField(null=True,blank=True)),
            ("owner",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,related_name="owned_incidents",to="auth.user")),
            ("resolution",models.TextField(blank=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
        ],
        options={"indexes":[models.Index(fields=["status","severity","-started_at"],name="incident_status_sev_idx")]},
    )]