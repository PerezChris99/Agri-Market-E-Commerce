from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("store","0010_national_area")]
    operations=[migrations.CreateModel(
        name="LogisticsHub",
        fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("name",models.CharField(max_length=200)),
            ("hub_type",models.CharField(max_length=20,default="collection",choices=[("collection","Collection Point"),("warehouse","Warehouse"),("distribution","Distribution Hub"),("cold_chain","Cold Chain Hub")])),
            ("address",models.TextField(blank=True)),
            ("latitude",models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
            ("longitude",models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
            ("capacity_units",models.PositiveIntegerField(default=0)),
            ("is_active",models.BooleanField(default=True)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("area",models.ForeignKey(null=True,blank=True,on_delete=django.db.models.deletion.PROTECT,related_name="logistics_hubs",to="store.administrativearea")),
        ],
        options={"indexes":[models.Index(fields=["area","hub_type","is_active"],name="hub_area_type_active_idx")]},
    )]