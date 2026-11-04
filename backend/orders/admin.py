"""Admin registration for carts and orders — lets staff inspect/manage both."""

from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    """Show a cart's items inline on the cart page."""

    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'total_price', 'updated_at')
    search_fields = ('user__email',)
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal')
    search_fields = ('cart__user__email', 'product__name')


class OrderItemInline(admin.TabularInline):
    """Show an order's line items inline on the order page (snapshots are
    read-only — historical records must not be edited)."""

    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity', 'subtotal')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__email')
    # order_number/total are system-generated snapshots; status is editable here.
    readonly_fields = ('order_number', 'user', 'total_price', 'shipping_address',
                       'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product_name', 'price', 'quantity', 'subtotal')
    search_fields = ('order__order_number', 'product_name')
