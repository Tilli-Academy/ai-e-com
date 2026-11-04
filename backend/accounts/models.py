"""
Database models for the accounts app.

- `User`    : our custom user, logging in with email instead of username.
- `Profile` : extra per-user info (phone, address) kept in a separate 1:1 table
              so the core auth model stays lean.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Custom user model.

    We inherit from AbstractUser (which already provides password handling,
    first/last name, is_staff, is_active, etc.) and change ONE thing: the login
    identifier is the email address, not a username.
    """

    # Remove the username field entirely — we don't use it.
    username = None

    # Email becomes the unique login identifier.
    email = models.EmailField('email address', unique=True)

    # Tell Django to authenticate with `email`.
    USERNAME_FIELD = 'email'

    # Fields prompted for by `createsuperuser` IN ADDITION to USERNAME_FIELD and
    # password. Empty because we only require email + password.
    REQUIRED_FIELDS = []

    # Wire in the custom manager defined in managers.py.
    objects = UserManager()

    def __str__(self):
        return self.email


class Profile(models.Model):
    """Extra profile information for a user (one profile per user)."""

    # OneToOneField = at most one Profile per User. CASCADE: if the user is
    # deleted, their profile is deleted too. related_name lets us do
    # `user.profile` in code.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user.email}'
