"""
Custom user manager.

A "manager" is the object you use to create/query model rows (e.g. User.objects
.create_user(...)). Django's default UserManager assumes a `username` field.
Because our User logs in with EMAIL instead, we must provide our own manager
that knows how to create users and superusers using the email as the identifier.
"""

from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for the custom email-based User model."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('An email address is required.')

        # normalize_email lowercases the domain part so Foo@Example.com and
        # foo@example.com are treated consistently.
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # set_password hashes the password (never store plain text).
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser (admin) with the given email/password."""
        # Superusers need these flags on; setdefault lets callers override.
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
