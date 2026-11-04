"""
URL routes for the shopping cart, mounted under /api/cart/ by config/urls.py.

    GET    /api/cart/              -> view cart
    POST   /api/cart/items/        -> add to cart
    PATCH  /api/cart/items/{id}/   -> update item quantity
    DELETE /api/cart/items/{id}/   -> remove item
    DELETE /api/cart/clear/        -> clear cart
"""

from django.urls import path

from .views import AddToCartView, CartItemDetailView, CartView, ClearCartView

urlpatterns = [
    path('', CartView.as_view(), name='cart'),
    path('clear/', ClearCartView.as_view(), name='cart-clear'),
    path('items/', AddToCartView.as_view(), name='cart-add-item'),
    path('items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
]
