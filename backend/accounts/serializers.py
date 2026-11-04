"""
Serializers for the accounts app.

A serializer validates incoming JSON and converts it to/from model instances.
Think of it as the "form + validation + JSON converter" layer for the API.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Profile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only-ish view of a user's core fields (safe to expose)."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_staff')
        read_only_fields = ('id', 'is_staff')


class RegisterSerializer(serializers.ModelSerializer):
    """Validates registration input and creates a User + its Profile."""

    # write_only => accepted on input but never sent back in responses.
    # validate_password runs Django's configured password strength checks.
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    # A confirmation field to catch typos. Not a model field, so declared here.
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, attrs):
        """Object-level validation: ensure the two passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {'password2': "The two password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        """Create the user (hashing the password) and an empty profile."""
        validated_data.pop('password2')          # not a model field
        password = validated_data.pop('password')

        # create_user (our custom manager) hashes the password correctly.
        user = User.objects.create_user(password=password, **validated_data)

        # Every user gets a profile row they can fill in later.
        Profile.objects.create(user=user)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    """View/update a user's profile. Nests the user's core fields read-only."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('id', 'user', 'phone', 'address', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login serializer.

    SimpleJWT's default already authenticates using USERNAME_FIELD (our email).
    We override `validate` only to enrich the login response with basic user
    info, so the frontend doesn't need a second request after logging in.
    """

    def validate(self, attrs):
        data = super().validate(attrs)          # returns {'access': ..., 'refresh': ...}
        data['user'] = UserSerializer(self.user).data
        return data
