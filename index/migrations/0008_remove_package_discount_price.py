"""Remove the deprecated Package.discount_price text field."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('index', '0007_migrate_discount_price_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='package',
            name='discount_price',
        ),
    ]
