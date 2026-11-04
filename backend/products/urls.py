"""
URL routes for the products app.

A DefaultRouter inspects each registered ViewSet and auto-generates the full
set of REST URLs. Registering `products` and `categories` below produces:

    GET/POST        /api/products/
    GET/PUT/PATCH/DELETE  /api/products/{slug}/
    GET/POST        /api/categories/
    GET/PUT/PATCH/DELETE  /api/categories/{slug}/

(The /api/ prefix is added where this module is included in config/urls.py.)
"""

from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = router.urls
