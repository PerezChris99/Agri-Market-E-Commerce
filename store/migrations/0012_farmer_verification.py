from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("store","0011_national_hub")]
    operations=[migrations.CreateModel(
        name="FarmerVerification",
        fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("verification_type",models.CharField(max_length=40,default="identity")),
            ("status",models.CharField(max_length=20,default="pending",choices=[("pending","Pending"),("verified","Verified"),("rejected","Rejected"),("suspended","Suspended")])),
            ("reference_hash",models.CharField(max_length=128,blank=True)),
            ("verified_at",models.DateTimeField(null=True,blank=True)),
            ("notes",models.TextField(blank=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("customer",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="farmer_verification",to="store.customer")),
            ("verified_by",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.SET_NULL,related_name="farmer_verifications",to="auth.user")),
        ],
    )]