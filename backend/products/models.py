"""
Database models for the products app.

- `Category` : groups products (e.g. "Electronics"). One category has many products.
- `Product`  : a catalog item with price, stock, image, etc.

Both models auto-generate a unique URL-friendly `slug` from their name.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


def unique_slugify(instance, value):
    """Return a slug based on `value` that is unique for instance's model.

    slugify("Gaming Laptop") -> "gaming-laptop". If that slug is already taken
    by another row, we append -1, -2, ... until we find a free one. This is how
    we guarantee unique product slugs even for similarly named products.
    """
    base = slugify(value) or 'item'
    ModelClass = instance.__class__
    slug = base
    counter = 1
    # Exclude the current row (instance.pk) so saving an existing object that
    # already owns the slug doesn't collide with itself.
    qs = ModelClass.objects.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


class Category(models.Model):
    """A product category. One category -> many products."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'   # avoids "categorys" in admin
        ordering = ('name',)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """A single catalog item."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()

    # DecimalField (never float) for money. Must be >= 0.01 — validated here at
    # the DB/model layer AND in the serializer for friendly API errors.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    # Stock can be 0 (out of stock) but never negative.
    stock = models.PositiveIntegerField(default=0)

    # The relationship. PROTECT => a category with products cannot be deleted.
    # related_name='products' lets us write category.products.all().
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
    )

    image = models.ImageField(upload_to='products/', blank=True, null=True)

    # Admins can hide a product from customers without deleting it.
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)   # newest first by default

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
