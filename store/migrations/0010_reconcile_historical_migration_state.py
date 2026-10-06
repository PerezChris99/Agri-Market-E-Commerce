from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Reconcile historical migration state with the current model state.

    The database schema already contains these objects through the historical
    migrations. The operations below update Django's migration state only;
    they intentionally perform no database DDL.
    """

    dependencies = [
        ('store', '0009_merge_store_migration_branches'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='deliveryrider',
                    name='user',
                    field=models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='delivery_rider',
                        to='auth.user',
                    ),
                ),
                migrations.AddField(
                    model_name='sellerprofile',
                    name='commission_rate',
                    field=models.DecimalField(
                        decimal_places=2,
                        default=10.0,
                        max_digits=5,
                    ),
                ),
                migrations.AddIndex(
                    model_name='deliveryzone',
                    index=models.Index(
                        fields=['is_active', 'region', 'name'],
                        name='zone_active_region_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='mobilemoneypayment',
                    index=models.Index(
                        fields=['order', 'status'],
                        name='momo_order_status_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='mobilemoneypayment',
                    index=models.Index(
                        fields=['external_reference'],
                        name='momo_external_ref_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='mobilemoneypayment',
                    index=models.Index(
                        fields=['provider_reference'],
                        name='momo_provider_ref_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='smsnotification',
                    index=models.Index(
                        fields=['status', '-created_at'],
                        name='sms_status_date_idx',
                    ),
                ),
                migrations.AddIndex(
                    model_name='smsnotification',
                    index=models.Index(
                        fields=['customer', '-created_at'],
                        name='sms_customer_date_idx',
                    ),
                ),
                migrations.AddConstraint(
                    model_name='deliveryzone',
                    constraint=models.UniqueConstraint(
                        fields=('name', 'region'),
                        name='unique_delivery_zone',
                    ),
                ),
            ],
        ),
    ]
