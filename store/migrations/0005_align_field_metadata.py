from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('store', '0004_order_inventory_commitment')]

    operations = [
        migrations.AlterField(
            model_name='customer', name='phone',
            field=models.CharField(blank=True, help_text='Format: 0700000000', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='customer', name='momo_phone',
            field=models.CharField(blank=True, help_text='MTN/Airtel number for payments', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='customer', name='receive_sms',
            field=models.BooleanField(default=True, help_text='Receive SMS notifications'),
        ),
        migrations.AlterField(
            model_name='customer', name='receive_whatsapp',
            field=models.BooleanField(default=True, help_text='Receive WhatsApp updates'),
        ),
        migrations.AlterField(
            model_name='shippingaddress', name='address',
            field=models.CharField(help_text='Street/Road, Building, etc.', max_length=300),
        ),
        migrations.AlterField(
            model_name='shippingaddress', name='delivery_notes',
            field=models.TextField(blank=True, help_text='Special delivery instructions'),
        ),
    ]
