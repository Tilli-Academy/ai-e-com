"""
Views for the shopping cart.

Every view operates strictly on `request.user`'s own cart, so one customer can
never see or modify another's cart. Writes that touch stock use transaction
.atomic() + select_for_update() to lock the product row — the same pattern
checkout will reuse to prevent overselling under concurrent requests.
"""

from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from products.models import Product
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    AddToCartSerializer,
    AdminOrderStatusSerializer,
    CartItemSerializer,
    CartSerializer,
    OrderSerializer,
    PlaceOrderSerializer,
    UpdateCartItemSerializer,
)


def get_user_cart(user):
    """Return the user's cart, creating it on first access.

    This guarantees every authenticated customer has exactly one cart without
    needing to create it at registration time.
    """
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    """GET /api/cart/ — view the current user's cart (auto-created)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_user_cart(request.user)
        return Response(CartSerializer(cart).data)


class AddToCartView(APIView):
    """POST /api/cart/items/ — add a product (or increment if already present)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_user_cart(request.user)
        serializer = AddToCartSerializer(data=request.data, context={'cart': cart})
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']

        # Lock the product row and the item so concurrent adds can't oversell.
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=product.pk)
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart, product=product, defaults={'quantity': quantity},
            )
            if not created:
                # Product already in cart -> increment (no duplicate row).
                item.quantity += quantity
                item.save()

        return Response(
            CartItemSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CartItemDetailView(APIView):
    """PATCH/DELETE /api/cart/items/{id}/ — update quantity or remove an item."""

    permission_classes = [IsAuthenticated]

    def get_item(self, request, pk):
        """Fetch the item ONLY from the caller's own cart (404 otherwise).

        Scoping by cart=request.user.cart is what prevents one user from
        updating/deleting another user's cart items.
        """
        cart = get_user_cart(request.user)
        return get_object_or_404(CartItem, pk=pk, cart=cart)

    def patch(self, request, pk):
        item = self.get_item(request, pk)
        serializer = UpdateCartItemSerializer(
            data=request.data, context={'cart_item': item}
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # Re-fetch under lock to validate against the latest stock.
            product = Product.objects.select_for_update().get(pk=item.product_id)
            new_qty = serializer.validated_data['quantity']
            if new_qty > product.stock:
                return Response(
                    {'quantity': [f'Only {product.stock} in stock.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.quantity = new_qty       # SET quantity (not increment)
            item.save()

        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        item = self.get_item(request, pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClearCartView(APIView):
    """DELETE /api/cart/clear/ — remove all items from the current user's cart."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_user_cart(request.user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Orders — checkout, history, detail, admin
# ---------------------------------------------------------------------------

# Legal status transitions. A status maps to the set of statuses it may move to.
# 'delivered' and 'cancelled' are terminal (no outgoing transitions). We never
# auto-set 'paid' — there is no payment gateway yet; an admin sets it manually.
ALLOWED_TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.PAID, Order.Status.PROCESSING, Order.Status.CANCELLED},
    Order.Status.PAID: {Order.Status.PROCESSING, Order.Status.CANCELLED},
    Order.Status.PROCESSING: {Order.Status.SHIPPED, Order.Status.CANCELLED},
    Order.Status.SHIPPED: {Order.Status.DELIVERED},
    Order.Status.DELIVERED: set(),
    Order.Status.CANCELLED: set(),
}


class OrderListCreateView(generics.ListAPIView):
    """GET  /api/orders/ — the current user's order history (newest first).
    POST /api/orders/ — place a new order from the user's cart (atomic)."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Scoped to the requesting user — customers see only their own orders.
        return Order.objects.filter(user=self.request.user).prefetch_related('items')

    def post(self, request, *args, **kwargs):
        # 1) Resolve the shipping address: request body, else profile, else error.
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipping = (serializer.validated_data.get('shipping_address') or '').strip()
        if not shipping:
            profile = getattr(request.user, 'profile', None)
            shipping = (profile.address or '').strip() if profile else ''
        if not shipping:
            raise ValidationError({'shipping_address':
                'A shipping address is required (none provided and no profile '
                'address on file).'})

        # 2) Everything below is one atomic unit: validate -> create -> deduct
        #    -> clear cart. Any error rolls the whole thing back.
        with transaction.atomic():
            cart = get_user_cart(request.user)
            cart_items = list(cart.items.select_related('product').all())

            # Prevent empty-cart checkout.
            if not cart_items:
                raise ValidationError({'detail': 'Your cart is empty.'})

            total = Decimal('0.00')
            validated = []
            for ci in cart_items:
                # Lock the product row so concurrent checkouts can't oversell.
                product = Product.objects.select_for_update().get(pk=ci.product_id)
                if not product.is_available:
                    raise ValidationError(
                        {'detail': f'"{product.name}" is no longer available.'})
                if ci.quantity > product.stock:
                    raise ValidationError({'detail':
                        f'Not enough stock for "{product.name}": requested '
                        f'{ci.quantity}, only {product.stock} available.'})
                total += product.price * ci.quantity
                validated.append((product, ci.quantity))

            # Create the order (status defaults to PENDING — never auto-paid).
            order = Order.objects.create(
                user=request.user, total_price=total, shipping_address=shipping,
            )
            # Snapshot each line and deduct stock.
            for product, qty in validated:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,   # snapshot
                    price=product.price,         # snapshot
                    quantity=qty,
                )
                product.stock -= qty
                product.save(update_fields=['stock'])

            # Clear the cart ONLY now, inside the committed transaction.
            cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/{order_number}/ — one order the user owns (404 otherwise)."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        # Scoping the queryset to the user means another user's order_number
        # simply isn't found -> 404. No cross-user access possible.
        return Order.objects.filter(user=self.request.user).prefetch_related('items')


class AdminOrderListView(generics.ListAPIView):
    """GET /api/orders/admin/all/ — all orders (staff only). Filter by status/user."""

    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().prefetch_related('items')
    filterset_fields = ('status', 'user')


class AdminOrderStatusView(APIView):
    """PATCH /api/orders/admin/{order_number}/ — update status (staff only)."""

    permission_classes = [IsAdminUser]

    def patch(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        serializer = AdminOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        # Enforce legal transitions (no jumping e.g. pending -> delivered).
        if new_status != order.status:
            allowed = ALLOWED_TRANSITIONS.get(order.status, set())
            if new_status not in allowed:
                nice = ', '.join(sorted(allowed)) or 'none (terminal state)'
                raise ValidationError({'status':
                    f"Cannot change status from '{order.status}' to "
                    f"'{new_status}'. Allowed next: {nice}."})

        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        return Response(OrderSerializer(order).data)
