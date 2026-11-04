"""
Serializers for the shopping cart.

Split by responsibility:
- Read serializers (CartSerializer, CartItemSerializer) shape the JSON we send
  back, including backend-computed subtotals/totals.
- Write serializers (AddToCartSerializer, UpdateCartItemSerializer) validate
  input: quantity > 0, product available, and quantity within stock.
"""

from rest_framework import serializers

from products.models import Product

from .models import CartItem, Order, OrderItem


class CartProductSerializer(serializers.ModelSerializer):
    """A compact product summary embedded inside each cart item."""

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'price', 'image', 'stock', 'is_available')


class CartItemSerializer(serializers.ModelSerializer):
    """Read representation of a cart line, with computed subtotal."""

    product = CartProductSerializer(read_only=True)
    # subtotal is a model @property; expose it read-only as money.
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'subtotal', 'added_at', 'updated_at')


class CartSerializer(serializers.Serializer):
    """Read representation of the whole cart with totals."""

    id = serializers.IntegerField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class AddToCartSerializer(serializers.Serializer):
    """Validate an 'add to cart' request: {product, quantity}."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)   # rejects 0 / negative

    def validate(self, attrs):
        product = attrs['product']
        quantity = attrs['quantity']

        if not product.is_available:
            raise serializers.ValidationError(
                {'product': 'This product is not available for purchase.'}
            )

        # The NEW total for this product = whatever is already in the cart plus
        # the amount being added. That combined amount must fit within stock.
        cart = self.context['cart']
        existing = CartItem.objects.filter(cart=cart, product=product).first()
        current_qty = existing.quantity if existing else 0
        requested_total = current_qty + quantity

        if requested_total > product.stock:
            raise serializers.ValidationError(
                {'quantity': f'Only {product.stock} in stock. '
                             f'You already have {current_qty} in your cart.'}
            )
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """Validate a quantity update: {quantity}. Sets (not increments) quantity."""

    quantity = serializers.IntegerField(min_value=1)   # rejects 0 / negative

    def validate_quantity(self, value):
        product = self.context['cart_item'].product
        if not product.is_available:
            raise serializers.ValidationError('This product is no longer available.')
        if value > product.stock:
            raise serializers.ValidationError(f'Only {product.stock} in stock.')
        return value


# ---------------------------------------------------------------------------
# Order serializers
# ---------------------------------------------------------------------------

class OrderItemSerializer(serializers.ModelSerializer):
    """Read representation of one order line (from stored snapshots)."""

    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    # product may be null if the product was later deleted — expose its id/slug
    # when present, but the snapshot fields (product_name, price) always remain.
    product_slug = serializers.SlugField(source='product.slug', read_only=True, default=None)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_slug', 'product_name',
                  'price', 'quantity', 'subtotal')


class OrderSerializer(serializers.ModelSerializer):
    """Read representation of a full order with its items."""

    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'order_number', 'status', 'total_price', 'total_items',
                  'shipping_address', 'items', 'created_at', 'updated_at')


class PlaceOrderSerializer(serializers.Serializer):
    """Validate checkout input. `shipping_address` is optional here; the view
    falls back to the profile address and errors if neither is available."""

    shipping_address = serializers.CharField(required=False, allow_blank=True)


class AdminOrderStatusSerializer(serializers.Serializer):
    """Validate an admin status change. Transition legality is checked in the
    view against ALLOWED_TRANSITIONS."""

    status = serializers.ChoiceField(choices=Order.Status.choices)
