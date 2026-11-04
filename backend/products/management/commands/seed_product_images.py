"""
Management command: `python manage.py seed_product_images`

Generates a simple local placeholder image for each product (solid colour +
the product name) using Pillow, saves it under MEDIA_ROOT/products/, and sets
the product's `image` field. This is a DEVELOPMENT utility to give the catalog
real image URLs — it does not use any external/network images and only fills
the empty `image` field (it never changes other product data).

Re-runnable: each product's image is written to products/<slug>.png and
overwritten in place.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw, ImageFont

from products.models import Product

# A small palette so different products get different colours (indexed by order).
PALETTE = [
    (79, 70, 229),    # indigo
    (14, 165, 233),   # sky
    (16, 185, 129),   # emerald
    (245, 158, 11),   # amber
    (239, 68, 68),    # red
    (139, 92, 246),   # violet
    (236, 72, 153),   # pink
    (34, 197, 94),    # green
]
SIZE = (600, 600)


def wrap(text, width=14):
    """Naive word-wrap so long names fit on the tile."""
    words, lines, line = text.split(), [], ''
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line.strip())
            line = w
        else:
            line += ' ' + w
    if line.strip():
        lines.append(line.strip())
    return '\n'.join(lines)


class Command(BaseCommand):
    help = 'Generate local placeholder images for all products (dev only).'

    def handle(self, *args, **options):
        out_dir = Path(settings.MEDIA_ROOT) / 'products'
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            font = ImageFont.load_default(size=44)
        except TypeError:
            # Older Pillow without size arg.
            font = ImageFont.load_default()

        count = 0
        for i, product in enumerate(Product.objects.all().order_by('id')):
            color = PALETTE[i % len(PALETTE)]
            img = Image.new('RGB', SIZE, color)
            draw = ImageDraw.Draw(img)

            text = wrap(product.name)
            # Centre the (multi-line) text.
            bbox = draw.multiline_textbbox((0, 0), text, font=font, align='center')
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pos = ((SIZE[0] - tw) / 2, (SIZE[1] - th) / 2)
            draw.multiline_text(pos, text, fill='white', font=font, align='center', spacing=10)

            fname = f'{product.slug}.png'
            img.save(out_dir / fname)
            product.image.name = f'products/{fname}'
            product.save(update_fields=['image'])
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Generated placeholder images for {count} products in {out_dir}.'
        ))
