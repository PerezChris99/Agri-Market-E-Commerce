from django.db import migrations


class Migration(migrations.Migration):
    """
    Merge the two historical store migration branches.

    The project previously contained independent 0003 migrations:
    - 0003_seller_settlement
    - 0003_contactmessage_delivery_newslettersubscriber_and_more

    Both histories are valid and must be preserved. This migration joins them
    without altering either branch.
    """

    dependencies = [
        ('store', '0003_contactmessage_delivery_newslettersubscriber_and_more'),
        ('store', '0008_postgres_search_indexes'),
    ]

    operations = []
