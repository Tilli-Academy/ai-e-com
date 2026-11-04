"""
Serializers for the products app.

They validate incoming data and shape the JSON responses. Note the two-way
`category` handling on ProductSerializer: clients WRITE a category id but READ
a nested category object — convenient for the frontend.
"""

from decimal import Decimal

from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """Serialize categories. `product_count` is computed, read-only."""

    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'product_count',
                  'created_at', 'updated_at')
        # slug is auto-generated in the model, so it's never required on input.
        read_only_fields = ('id', 'slug', 'product_count', 'created_at', 'updated_at')


class ProductSerializer(serializers.ModelSerializer):
    """Serialize products.

    - `category`        : writable, accepts a Category primary key (id).
    - `category_detail` : read-only nested category, so responses are rich.
    """

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'description', 'price', 'stock',
                  'category', 'category_detail', 'image', 'is_available',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def validate_price(self, value):
        """Reject zero/negative prices with a clear message."""
        if value < Decimal('0.01'):
            raise serializers.ValidationError('Price must be greater than 0.')
        return value

    def validate_stock(self, value):
        """Stock may be 0 but never negative."""
        if value < 0:
            raise serializers.ValidationError('Stock cannot be negative.')
        return value
