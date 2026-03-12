"""Custom template tags and filters for the myadmin app."""

from django import template

from index.models import Package

register = template.Library()


@register.filter(name='to_list')
def to_list(value, delimiter=','):
    """Split a string into a list using the given delimiter."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]


@register.simple_tag
def min_max_price(package):
    """Return [min_price, max_price] from a package's pricing tiers."""
    tiers = package.pricing_tiers.all()
    if not tiers:
        return [0, 0]
    prices = [t.price for t in tiers]
    return [min(prices), max(prices)]


@register.simple_tag
def get_price(package):
    """Return list of [adult_count, children_count, price] for each pricing tier."""
    tiers = package.pricing_tiers.order_by('min_adult_count', 'min_children_count')
    return [[t.min_adult_count, t.min_children_count, t.price] for t in tiers]
