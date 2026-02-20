"""Custom template tags and filters for the myadmin app."""

from django import template

register = template.Library()


@register.filter(name='to_list')
def to_list(value, delimiter=','):
    """Split a string into a list using the given delimiter."""
    if not value:
        return []
    return [item.strip() for item in str(value).split(delimiter) if item.strip()]
