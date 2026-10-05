from django.db import migrations


def install_trigram_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    schema_editor.execute('CREATE INDEX IF NOT EXISTS product_name_trgm_idx ON store_product USING gin (name gin_trgm_ops)')
    schema_editor.execute('CREATE INDEX IF NOT EXISTS product_description_trgm_idx ON store_product USING gin (description gin_trgm_ops)')


def remove_trigram_indexes(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute('DROP INDEX IF EXISTS product_name_trgm_idx')
    schema_editor.execute('DROP INDEX IF EXISTS product_description_trgm_idx')


class Migration(migrations.Migration):
    dependencies = [('store', '0007_performance_constraints')]
    operations = [migrations.RunPython(install_trigram_indexes, remove_trigram_indexes)]
