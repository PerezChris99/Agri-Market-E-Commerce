from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PromoRedemption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('redeemed_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='promo_redemptions', to='store.customer')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='promo_redemption', to='store.order')),
                ('promo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='redemptions', to='store.promocode')),
            ],
            options={'ordering': ['-redeemed_at']},
        ),
        migrations.AddConstraint(
            model_name='promoredemption',
            constraint=models.UniqueConstraint(fields=('promo', 'order'), name='unique_promo_order_redemption'),
        ),
    ]
