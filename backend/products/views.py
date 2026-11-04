"""
ViewSets for the products app.

A ModelViewSet provides list/retrieve/create/update/destroy in one class. The
DefaultRouter (see urls.py) maps them to standard REST URLs automatically.
"""

from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from .filters import ProductFilter
from .models import Category, Product
from .permissions import IsAdminOrReadOnly
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for categories. Read = public, write = staff only."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'   # URLs use the slug, e.g. /api/categories/electronics/

    def destroy(self, request, *args, **kwargs):
        """Delete a category, but turn the PROTECT error into a clean 409.

        Because Product.category uses on_delete=PROTECT, deleting a category
        that still has products raises ProtectedError (an HTTP 500 by default).
        We catch it and return a helpful 409 Conflict instead.
        """
        instance = self.get_object()
        try:
            instance.delete()
        except ProtectedError:
            return Response(
                {'detail': 'Cannot delete this category because it still has '
                           'products. Reassign or delete those products first.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD for products with search, filtering and ordering.

    Read = public, write = staff only (IsAdminOrReadOnly).
    """

    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'

    # Filtering stack (DjangoFilterBackend/Search/Ordering are global defaults):
    filterset_class = ProductFilter               # category, price range, in_stock
    search_fields = ('name', 'description')        # ?search=
    ordering_fields = ('price', 'created_at', 'name')
    ordering = ('-created_at',)                    # default ordering

    def get_queryset(self):
        """Customers see only AVAILABLE products; staff see everything.

        This enforces "customers can view available products" at the data layer,
        so hidden/unavailable items never leak into public responses.
        """
        qs = Product.objects.select_related('category')
        user = self.request.user
        if user and user.is_staff:
            return qs
        return qs.filter(is_available=True)
