"""
URL routes for order management, mounted under /api/orders/ by config/urls.py.

Kept separate from urls.py (which serves the cart under /api/cart/) so the two
feature areas of this app have clean, independent URL prefixes.

    GET    /api/orders/                      -> the current user's order history
    POST   /api/orders/                      -> place an order (from the cart)
    GET    /api/orders/{order_number}/       -> one of the user's orders
    GET    /api/orders/admin/all/            -> all orders (staff only)
    PATCH  /api/orders/admin/{order_number}/ -> update order status (staff only)
"""

from django.urls import path

from .views import (
    AdminOrderListView,
    AdminOrderStatusView,
    OrderDetailView,
    OrderListCreateView,
)

urlpatterns = [
    # Admin routes first so 'admin' isn't captured as an {order_number}.
    path('admin/all/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/<str:order_number>/', AdminOrderStatusView.as_view(), name='admin-order-status'),

    path('', OrderListCreateView.as_view(), name='order-list-create'),   # GET history / POST checkout
    path('<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
]
