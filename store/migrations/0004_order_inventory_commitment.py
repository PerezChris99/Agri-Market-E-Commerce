from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('store', '0003_seller_settlement')]

    operations = [
        migrations.AddField(
            model_name='order',
            name='inventory_committed',
            field=models.BooleanField(default=False),
        ),
    ]
