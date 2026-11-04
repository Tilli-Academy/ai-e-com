"""
Filter definitions for the products list endpoint.

django-filter turns query-string parameters into ORM filters. This FilterSet
adds price-range, stock, and category filtering on top of the SearchFilter
(name/description) and OrderingFilter configured on the view.

Examples:
    /api/products/?category=2
    /api/products/?min_price=10&max_price=50
    /api/products/?in_stock=true
"""

import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    # `price__gte` / `price__lte` lookups, exposed as friendly param names.
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    # ?in_stock=true -> only products with stock > 0.
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Product
        # Exact-match filters generated automatically for these fields.
        fields = ('category', 'is_available')

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset
