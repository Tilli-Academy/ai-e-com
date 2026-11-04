"""
Management command: `python manage.py seed_products`

Inserts a few sample categories and products so the listing/search/filter
endpoints have realistic data to return. Safe to re-run — it uses get_or_create
so it won't create duplicates.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import Category, Product


class Command(BaseCommand):
    help = 'Seed the database with sample categories and products.'

    def handle(self, *args, **options):
        categories = {
            'Electronics': 'Phones, laptops and gadgets',
            'Books': 'Fiction and non-fiction',
            'Home & Kitchen': 'Appliances and essentials',
        }
        cat_objs = {}
        for name, desc in categories.items():
            cat, _ = Category.objects.get_or_create(
                name=name, defaults={'description': desc}
            )
            cat_objs[name] = cat

        products = [
            ('Wireless Headphones', 'Noise-cancelling over-ear headphones',
             Decimal('79.99'), 25, 'Electronics', True),
            ('Gaming Laptop', '15-inch laptop with dedicated GPU',
             Decimal('1299.00'), 8, 'Electronics', True),
            ('Smartphone', '128GB, dual camera',
             Decimal('499.50'), 0, 'Electronics', True),     # out of stock
            ('Python Crash Course', 'Beginner-friendly programming book',
             Decimal('29.95'), 100, 'Books', True),
            ('The Pragmatic Programmer', 'Classic software engineering book',
             Decimal('42.00'), 40, 'Books', True),
            ('Electric Kettle', '1.7L stainless steel kettle',
             Decimal('24.99'), 60, 'Home & Kitchen', True),
            ('Discontinued Blender', 'Old model, hidden from customers',
             Decimal('19.99'), 5, 'Home & Kitchen', False),  # unavailable
        ]

        created = 0
        for name, desc, price, stock, cat_name, available in products:
            obj, was_created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'price': price,
                    'stock': stock,
                    'category': cat_objs[cat_name],
                    'is_available': available,
                },
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {Category.objects.count()} categories, '
            f'{Product.objects.count()} products ({created} new).'
        ))
