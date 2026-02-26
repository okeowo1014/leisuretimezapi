"""
Custom pagination classes for the Leisuretimez API.
"""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default pagination with a capped max page size.

    Prevents clients from requesting excessively large pages
    (e.g. ``?page_size=999999``) which would cause heavy DB queries.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
