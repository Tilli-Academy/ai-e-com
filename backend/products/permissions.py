"""
Custom permission for the products app.

The project's global default is IsAuthenticated (everything locked down). For
the catalog we want the opposite for reads: anyone may browse, but only staff
may change data. This permission class expresses exactly that.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only access to anyone; write access only to staff users."""

    def has_permission(self, request, view):
        # SAFE_METHODS = GET, HEAD, OPTIONS -> always allowed (public browsing).
        if request.method in permissions.SAFE_METHODS:
            return True
        # Writes (POST/PUT/PATCH/DELETE) require an authenticated staff user.
        return bool(request.user and request.user.is_staff)
