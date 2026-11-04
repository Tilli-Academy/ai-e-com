"""
Root URL configuration.

Every incoming request's path is matched against the patterns below, in order.
As we add apps in later phases, we `include()` their own urls.py here so each
app owns its routes (clean separation).
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Simple endpoint to confirm the API server is alive.

    Returns a small JSON payload. Useful for quick manual testing and for
    uptime monitoring. We keep it dependency-free so it works even before any
    app or database table exists.
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'ai-ecommerce-backend',
        'debug': settings.DEBUG,
    })


urlpatterns = [
    # Django's built-in admin site (we use it for staff management in Phase 5).
    path('admin/', admin.site.urls),

    # Health probe — open in a browser at http://localhost:8000/api/health/
    path('api/health/', health_check, name='health-check'),

    # Authentication endpoints (Phase 2).
    path('api/auth/', include('accounts.urls')),

    # Product catalog endpoints (Phase 3). The router already namespaces
    # /products/ and /categories/, so we include it directly under /api/.
    path('api/', include('products.urls')),

    # Shopping cart endpoints (Phase 4).
    path('api/cart/', include('orders.urls')),

    # Order management endpoints (Phase 5). Same app, separate URL module.
    path('api/orders/', include('orders.order_urls')),

    # AI shopping assistant endpoints (Phase 7).
    path('api/assistant/', include('assistant.urls')),
]

# In development, let Django serve uploaded media files (product images).
# In production this is handled by the web server instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
