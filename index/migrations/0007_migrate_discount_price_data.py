"""Data migration: move Package.discount_price text into PricingTier rows."""

from decimal import Decimal

from django.db import migrations


def forwards(apps, schema_editor):
    Package = apps.get_model('index', 'Package')
    PricingTier = apps.get_model('index', 'PricingTier')

    for package in Package.objects.exclude(discount_price__isnull=True).exclude(discount_price=''):
        raw = package.discount_price.strip()
        if not raw:
            continue
        for segment in raw.split('-'):
            parts = segment.split(',')
            if len(parts) < 3:
                continue
            PricingTier.objects.create(
                package=package,
                min_adult_count=int(parts[0]),
                min_children_count=int(parts[1]),
                price=Decimal(parts[2]),
            )


def backwards(apps, schema_editor):
    Package = apps.get_model('index', 'Package')
    PricingTier = apps.get_model('index', 'PricingTier')

    for package in Package.objects.all():
        tiers = PricingTier.objects.filter(package=package).order_by(
            'min_adult_count', 'min_children_count'
        )
        if tiers.exists():
            segments = [
                f'{t.min_adult_count},{t.min_children_count},{t.price}'
                for t in tiers
            ]
            package.discount_price = '-'.join(segments)
            package.save(update_fields=['discount_price'])


class Migration(migrations.Migration):
    dependencies = [
        ('index', '0006_add_pricing_tier'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
