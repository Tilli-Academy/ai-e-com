"""
Management command: `python manage.py seed_faqs`

Inserts sample FAQ entries the assistant can answer from. Safe to re-run — uses
get_or_create keyed on the question, so it never duplicates or overwrites.
"""

from django.core.management.base import BaseCommand

from assistant.models import FAQ

FAQS = [
    {
        'question': 'How long does shipping take?',
        'answer': 'Standard shipping usually takes 3–5 business days. You will '
                  'get a tracking update once your order ships.',
        'keywords': 'shipping,delivery,ship,how long,arrive,dispatch',
    },
    {
        'question': 'What is your return policy?',
        'answer': 'You can return most items within 30 days of delivery for a '
                  'full refund, as long as they are in original condition.',
        'keywords': 'return,refund,exchange,money back,policy',
    },
    {
        'question': 'What payment methods are accepted?',
        'answer': 'This is a demo store, so no real payments are processed yet. '
                  'Orders are placed with a Pending status for now.',
        'keywords': 'payment,pay,card,credit,method,checkout',
    },
    {
        'question': 'How do I track my order?',
        'answer': 'Sign in and open "My Orders" to see each order and its '
                  'current status (Pending, Processing, Shipped, etc.).',
        'keywords': 'track,tracking,order status,where is my order,my orders',
    },
    {
        'question': 'How do I create an account?',
        'answer': 'Click "Sign up", enter your email, name, and a password, and '
                  'you will be signed in automatically.',
        'keywords': 'account,register,sign up,signup,create account',
    },
    {
        'question': 'Do I need an account to place an order?',
        'answer': 'Yes — you need to be signed in to add items to your cart and '
                  'to check out, so your orders are saved to your account.',
        'keywords': 'account required,guest,checkout,sign in,login',
    },
]


class Command(BaseCommand):
    help = 'Seed sample FAQ entries for the assistant.'

    def handle(self, *args, **options):
        created = 0
        for item in FAQS:
            _, was_created = FAQ.objects.get_or_create(
                question=item['question'],
                defaults={'answer': item['answer'], 'keywords': item['keywords']},
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {FAQ.objects.count()} FAQs total ({created} new).'
        ))
