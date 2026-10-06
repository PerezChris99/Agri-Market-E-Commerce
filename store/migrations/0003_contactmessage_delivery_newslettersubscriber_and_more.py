from django.db import migrations


class Migration(migrations.Migration):
    """
    Historical compatibility migration.

    The initial migration already contained the objects represented by the
    original 0003 contact/delivery migration. The migration is retained as a
    no-op so existing migration records remain valid without replaying
    duplicate DDL on fresh databases.
    """

    dependencies = [
        ('store', '0002_deliveryzone_customer_alternate_phone_and_more'),
    ]

    operations = []
