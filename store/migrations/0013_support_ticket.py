from django.db import migrations, models
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    dependencies=[("store","0012_farmer_verification")]
    operations=[migrations.CreateModel(
        name="SupportTicket",
        fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("ticket_id",models.UUIDField(default=uuid.uuid4,editable=False,unique=True)),
            ("subject",models.CharField(max_length=200)),
            ("description",models.TextField()),
            ("priority",models.CharField(max_length=10,default="normal",choices=[("low","Low"),("normal","Normal"),("high","High"),("critical","Critical")])),
            ("status",models.CharField(max_length=12,default="open",choices=[("open","Open"),("assigned","Assigned"),("pending","Pending"),("resolved","Resolved"),("closed","Closed")])),
            ("resolution",models.TextField(blank=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("assigned_to",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,related_name="support_tickets",to="auth.user")),
            ("customer",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,related_name="support_tickets",to="store.customer")),
        ],
        options={"indexes":[models.Index(fields=["status","priority","-created_at"],name="ticket_status_priority_idx")]},
    )]