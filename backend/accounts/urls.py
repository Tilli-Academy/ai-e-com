"""
URL routes for the accounts app.

These are mounted under /api/auth/ by config/urls.py, so e.g. the `register`
route below becomes the full path /api/auth/register/.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, ProfileView, RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    # Exchange a valid refresh token for a new access token (SimpleJWT built-in).
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
