"""
Database models for the orders app (cart + orders).

Relationships:
    User --(1:1)-- Cart  --(1:N)-- CartItem  --(N:1)-- Product
    User --(1:N)-- Order --(1:N)-- OrderItem --(N:1)-- Product (nullable snapshot)

Money is always computed here on the backend using Decimal arithmetic — the
frontend never sends prices. Orders store name/price SNAPSHOTS so historical
orders stay accurate even if the catalog changes later.
"""

import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


class Cart(models.Model):
    """One shopping cart per user (OneToOne)."""

    # settings.AUTH_USER_MODEL = our custom accounts.User. Using the setting
    # (not a direct import) is the Django-recommended way to reference the user.
    # CASCADE: if the user is deleted, their cart goes too.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_items(self):
        """Total number of units across all items (sum of quantities)."""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Grand total = sum of every item's subtotal. Returns a Decimal."""
        total = sum((item.subtotal for item in self.items.all()), Decimal('0.00'))
        return total

    def __str__(self):
        return f'Cart of {self.user.email}'


class CartItem(models.Model):
    """A single line in a cart: a product + how many of it."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,       # removing a cart removes its items
        related_name='items',
    )
    # CASCADE: deleting a product removes it from any carts (but the carts and
    # their other items remain — only the affected line disappears).
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # A product may appear at most ONCE per cart — adding an existing product
        # increments its quantity instead of creating a duplicate row.
        unique_together = ('cart', 'product')
        ordering = ('added_at',)

    @property
    def subtotal(self):
        """Line subtotal = current product price × quantity (Decimal)."""
        return self.product.price * self.quantity

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'


# ---------------------------------------------------------------------------
# Orders (checkout & history)
# ---------------------------------------------------------------------------

def generate_order_number():
    """Return a unique, human-friendly order number, e.g. ORD-20261103-7F3A9C.

    Format: ORD-<YYYYMMDD>-<6 random hex chars>. On the rare chance of a
    collision we simply try again until we find a free one.
    """
    date_part = timezone.now().strftime('%Y%m%d')
    while True:
        random_part = secrets.token_hex(3).upper()   # 6 hex chars
        number = f'ORD-{date_part}-{random_part}'
        if not Order.objects.filter(order_number=number).exists():
            return number


class Order(models.Model):
    """A placed order — a permanent record of a completed checkout."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    # PROTECT: a customer who has orders cannot be deleted, preserving history.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
    )
    order_number = models.CharField(max_length=32, unique=True, editable=False)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING,
    )
    # Snapshot of the grand total at checkout (never recomputed from live prices).
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    # Snapshot of where it ships — stays correct even if the profile changes.
    shipping_address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)   # newest first

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    """A single line in an order. Stores SNAPSHOTS so it never changes later."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items',
    )
    # SET_NULL: if the product is later deleted, keep the line (we have the
    # snapshots); the link just becomes null.
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
    )
    # Snapshots captured at checkout — the source of truth for this line forever.
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        """Line subtotal from the SNAPSHOT price (not the live product price)."""
        return self.price * self.quantity

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'
