"""
Views for the accounts app — one per endpoint.

DRF generic views do most of the heavy lifting:
- CreateAPIView        -> handles POST (create)
- RetrieveUpdateAPIView-> handles GET + PUT/PATCH
We only specify the serializer, permissions, and (where needed) the object.
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    ProfileSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — create a new account. Public."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]   # anyone may register (overrides global default)


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — return access + refresh tokens. Public.

    Subclasses SimpleJWT's view but swaps in our serializer so the response
    also includes basic user info.
    """

    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the supplied refresh token.

    The client sends the refresh token it wants to invalidate. Once blacklisted,
    it can no longer be used to mint new access tokens. Requires a valid access
    token to call (so only a logged-in user can log themselves out).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'The "refresh" token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'detail': 'Invalid or expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_205_RESET_CONTENT,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/auth/profile/ — the logged-in user's own profile.

    Protected (IsAuthenticated inherited from the global default). We return the
    CURRENT user's profile by overriding get_object, so a user can never read or
    edit someone else's profile.
    """

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
