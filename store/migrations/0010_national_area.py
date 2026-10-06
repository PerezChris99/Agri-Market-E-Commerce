from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("store", "0009_merge_store_migration_branches")]
    operations = [
        migrations.CreateModel(
            name="AdministrativeArea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(max_length=50, unique=True)),
                ("level", models.CharField(max_length=20, choices=[("country","Country"),("region","Region"),("district","District"),("county","County"),("subcounty","Subcounty"),("parish","Parish")])),
                ("country_code", models.CharField(max_length=2, default="UG")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("parent", models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name="children", to="store.administrativearea")),
            ],
            options={"ordering":["level","name"],"indexes":[models.Index(fields=["level","is_active","name"],name="area_level_active_name_idx")]},
        ),
    ]
