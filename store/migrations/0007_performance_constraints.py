from django.db import migrations, models
from django.db.models import Q

def normalize_delivery_zone_regions(apps, schema_editor):
    DeliveryZone = apps.get_model('store', 'DeliveryZone')
    mapping = {'Central Region':'central','Eastern Region':'eastern','Northern Region':'northern','Western Region':'western','Kampala Metropolitan':'kampala'}
    for old, new in mapping.items(): DeliveryZone.objects.filter(region=old).update(region=new)

class Migration(migrations.Migration):
    dependencies = [('store', '0006_operations')]
    operations = [
        migrations.RunPython(normalize_delivery_zone_regions, migrations.RunPython.noop),
        migrations.AddIndex(model_name='category', index=models.Index(fields=['is_active','name'], name='category_active_name_idx')),
        migrations.AddIndex(model_name='product', index=models.Index(fields=['is_active','-created_at'], name='product_active_date_idx')),
        migrations.AddIndex(model_name='product', index=models.Index(fields=['is_featured','is_active','-created_at'], name='product_featured_idx')),
        migrations.AddIndex(model_name='product', index=models.Index(fields=['category','is_active','-created_at'], name='product_category_idx')),
        migrations.AddIndex(model_name='product', index=models.Index(fields=['price'], name='product_price_idx')),
        migrations.AddIndex(model_name='product', index=models.Index(fields=['name'], name='product_name_idx')),
        migrations.AddConstraint(model_name='order', constraint=models.UniqueConstraint(condition=Q(complete=False, customer__isnull=False), fields=('customer',), name='unique_open_customer_order')),
        migrations.AddIndex(model_name='order', index=models.Index(fields=['customer','complete','-date_ordered'], name='order_customer_open_idx')),
        migrations.AddIndex(model_name='order', index=models.Index(fields=['status','-date_ordered'], name='order_status_date_idx')),
        migrations.AddIndex(model_name='order', index=models.Index(fields=['payment_status','-date_ordered'], name='order_payment_date_idx')),
        migrations.AddConstraint(model_name='orderitem', constraint=models.UniqueConstraint(fields=('order','product'), name='unique_order_product')),
        migrations.AddIndex(model_name='orderitem', index=models.Index(fields=['product','-date_added'], name='orderitem_product_date_idx')),
        migrations.AlterUniqueTogether(name='wishlist', unique_together=set()),
        migrations.AddConstraint(model_name='wishlist', constraint=models.UniqueConstraint(fields=('customer','product'), name='unique_wishlist_customer_product')),
        migrations.AddIndex(model_name='wishlist', index=models.Index(fields=['customer','-date_added'], name='wishlist_customer_date_idx')),
        migrations.AlterUniqueTogether(name='review', unique_together=set()),
        migrations.AddConstraint(model_name='review', constraint=models.UniqueConstraint(fields=('product','customer'), name='unique_review_product_customer')),
        migrations.AddIndex(model_name='review', index=models.Index(fields=['product','is_approved','-created_at'], name='review_product_idx')),
        migrations.AddIndex(model_name='review', index=models.Index(fields=['customer','-created_at'], name='review_customer_idx')),
        migrations.AddConstraint(model_name='deliveryzone', constraint=models.UniqueConstraint(fields=('name','region'), name='unique_delivery_zone')),
        migrations.AddIndex(model_name='deliveryzone', index=models.Index(fields=['is_active','region','name'], name='zone_active_region_idx')),
        migrations.AddIndex(model_name='mobilemoneypayment', index=models.Index(fields=['order','status'], name='momo_order_status_idx')),
        migrations.AddIndex(model_name='mobilemoneypayment', index=models.Index(fields=['external_reference'], name='momo_external_ref_idx')),
        migrations.AddIndex(model_name='mobilemoneypayment', index=models.Index(fields=['provider_reference'], name='momo_provider_ref_idx')),
        migrations.AddIndex(model_name='smsnotification', index=models.Index(fields=['status','-created_at'], name='sms_status_date_idx')),
        migrations.AddIndex(model_name='smsnotification', index=models.Index(fields=['customer','-created_at'], name='sms_customer_date_idx')),
        migrations.AddIndex(model_name='sellerorder', index=models.Index(fields=['seller','payout_status','-created_at'], name='sellerorder_payout_idx')),
        migrations.AddIndex(model_name='sellerorder', index=models.Index(fields=['status','-created_at'], name='sellerorder_status_idx')),
    ]
