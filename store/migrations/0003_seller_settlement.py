from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0002_promoredemption'),
    ]

    operations = [
        migrations.AddField(
            model_name='sellerprofile',
            name='commission_rate',
            field=models.DecimalField(decimal_places=2, default=10.0, max_digits=5),
        ),
        migrations.CreateModel(
            name='SellerOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('commission_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('seller_amount', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('payout_status', models.CharField(choices=[('pending', 'Pending'), ('eligible', 'Eligible'), ('paid', 'Paid'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_orders', to='store.order')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='seller_orders', to='store.sellerprofile')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='sellerorder',
            constraint=models.UniqueConstraint(fields=('order', 'seller'), name='unique_order_seller'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='seller_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='store.sellerorder'),
        ),
        migrations.CreateModel(
            name='SellerPayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('paid', 'Paid'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('provider_reference', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payouts', to='store.sellerprofile')),
                ('seller_order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='payout', to='store.sellerorder')),
            ],
        ),
    ]
