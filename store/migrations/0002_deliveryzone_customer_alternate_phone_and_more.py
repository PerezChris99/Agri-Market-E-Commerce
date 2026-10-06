from django.db import migrations


class Migration(migrations.Migration):
    """
    Historical compatibility migration.

    The initial migration already contained these schema objects. This
    migration is intentionally a no-op so fresh installations do not attempt
    to create duplicate tables/columns while existing databases retain their
    recorded migration history.
    """

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = []
