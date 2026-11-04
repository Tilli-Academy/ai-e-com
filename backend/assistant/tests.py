"""
Tests for the assistant (7.1 + 7.2). Ollama is MOCKED so these run fast and
deterministically. They verify:
  - graceful fallback when Ollama is down,
  - rule-based intent detection (faq / product / general),
  - that grounding injects REAL product/FAQ data into the prompt,
  - that unavailable products are never surfaced.
"""

from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from orders.models import Order, OrderItem
from products.models import Category, Product

from .models import FAQ
from .services import intent as intent_service
from .services.ollama_client import OllamaError


class AssistantTestData(APITestCase):
    """Shared fixtures: a category, products (one hidden), and a FAQ."""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name='Electronics')
        cls.books = Category.objects.create(name='Books')
        cls.kitchen = Category.objects.create(name='Home & Kitchen')

        cls.laptop = Product.objects.create(
            name='Gaming Laptop', description='Powerful laptop for gaming',
            price=Decimal('1299.00'), stock=8, category=cls.cat, is_available=True,
        )
        cls.headphones = Product.objects.create(
            name='Wireless Headphones', description='Over-ear headphones',
            price=Decimal('79.99'), stock=25, category=cls.cat, is_available=True,
        )
        cls.phone = Product.objects.create(      # OUT OF STOCK
            name='Smartphone', description='Dual camera phone',
            price=Decimal('499.50'), stock=0, category=cls.cat, is_available=True,
        )
        cls.hidden = Product.objects.create(     # UNAVAILABLE
            name='Secret Prototype', description='not for sale',
            price=Decimal('9.99'), stock=5, category=cls.cat, is_available=False,
        )
        cls.cheap_book = Product.objects.create(
            name='Python Crash Course', description='Beginner programming book',
            price=Decimal('29.95'), stock=100, category=cls.books, is_available=True,
        )
        cls.pricey_book = Product.objects.create(
            name='Expensive Tome', description='A costly reference book',
            price=Decimal('42.00'), stock=5, category=cls.books, is_available=True,
        )
        cls.kettle = Product.objects.create(
            name='Electric Kettle', description='1.7L stainless steel kettle',
            price=Decimal('24.99'), stock=59, category=cls.kitchen, is_available=True,
        )
        cls.faq = FAQ.objects.create(
            question='What is your return policy?',
            answer='You can return most items within 30 days of delivery.',
            keywords='return,refund,policy',
        )


class IntentDetectionTests(AssistantTestData):
    def test_product_intent(self):
        data = intent_service.detect_intent('How much is the Gaming Laptop?')
        self.assertEqual(data['intent'], 'product')
        self.assertIn(self.laptop, data['products'])

    def test_search_excludes_unavailable_products(self):
        results = intent_service.search_products('secret prototype')
        self.assertNotIn(self.hidden, results)

    def test_faq_intent(self):
        data = intent_service.detect_intent('What is your return policy?')
        self.assertEqual(data['intent'], 'faq')
        self.assertIn(self.faq, data['faqs'])

    def test_general_intent(self):
        data = intent_service.detect_intent('hello there')
        self.assertEqual(data['intent'], 'general')

    def test_order_status_intent_by_phrase(self):
        data = intent_service.detect_intent('Where is my order?')
        self.assertEqual(data['intent'], 'order_status')

    def test_order_status_intent_by_number(self):
        data = intent_service.detect_intent('status of order ORD-20261104-AB12CD')
        self.assertEqual(data['intent'], 'order_status')
        self.assertEqual(data['order_number'], 'ORD-20261104-AB12CD')

    def test_track_my_order_howto_not_order_status(self):
        # Regression: the how-to question must NOT be hijacked by order_status
        # detection (in production it routes to the seeded "track my order" FAQ).
        data = intent_service.detect_intent('How do I track my order?')
        self.assertNotEqual(data['intent'], 'order_status')

    def test_unstocked_product_routes_to_product_with_no_matches(self):
        # "do you sell X" with no matching product -> product intent, empty list
        # (so the prompt tells the model we don't carry it, preventing invention).
        data = intent_service.detect_intent('Do you sell refrigerators?')
        self.assertEqual(data['intent'], 'product')
        self.assertEqual(list(data['products']), [])
        self.assertEqual(data['faqs'], [])


class RecommendationTests(AssistantTestData):
    def test_extract_max_price(self):
        self.assertEqual(intent_service.extract_max_price('electronics under $100'), Decimal('100'))
        self.assertEqual(intent_service.extract_max_price('books below 40'), Decimal('40'))
        self.assertEqual(intent_service.extract_max_price('a $50 gift'), Decimal('50'))
        self.assertIsNone(intent_service.extract_max_price('recommend a laptop'))

    def test_extract_category(self):
        self.assertEqual(intent_service.extract_category('show kitchen products'), self.kitchen)
        self.assertEqual(intent_service.extract_category('recommend electronics'), self.cat)
        self.assertIsNone(intent_service.extract_category('recommend something nice'))

    def test_recommend_electronics_under_100(self):
        products, criteria = intent_service.recommend_products('Recommend electronics under $100')
        self.assertIn(self.headphones, products)   # $79.99, in stock
        self.assertNotIn(self.laptop, products)    # $1299 > budget
        self.assertNotIn(self.phone, products)     # out of stock
        self.assertEqual(criteria['max_price'], Decimal('100'))

    def test_recommend_books_below_40(self):
        products, _ = intent_service.recommend_products('Suggest books below $40')
        self.assertIn(self.cheap_book, products)     # $29.95
        self.assertNotIn(self.pricey_book, products) # $42 > 40

    def test_recommend_kitchen_excludes_unavailable_and_oos(self):
        products, _ = intent_service.recommend_products('Show available kitchen products')
        self.assertIn(self.kettle, products)
        self.assertTrue(all(p.is_available and p.stock > 0 for p in products))

    def test_recommend_a_laptop_by_name(self):
        products, _ = intent_service.recommend_products('Recommend a laptop')
        self.assertEqual(products[0], self.laptop)

    def test_detect_recommendation_intent(self):
        data = intent_service.detect_intent('Recommend electronics under $100')
        self.assertEqual(data['intent'], 'recommendation')


class RecommendationsEndpointTests(AssistantTestData):
    url = '/api/assistant/recommendations/'

    def test_returns_only_available_in_stock_products(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        products = res.data['products']
        self.assertGreater(len(products), 0)
        # Never recommend out-of-stock or unavailable items.
        for p in products:
            self.assertTrue(p['is_available'])
            self.assertGreater(p['stock'], 0)
        names = [p['name'] for p in products]
        self.assertNotIn('Smartphone', names)        # stock 0
        self.assertNotIn('Secret Prototype', names)  # unavailable
        # Full product shape (for ProductCard) is present.
        self.assertIn('category_detail', products[0])
        self.assertIn('image', products[0])


class OrderStatusSecurityTests(AssistantTestData):
    """Authentication + privacy for order-status queries."""

    url = '/api/assistant/chat/'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        User = get_user_model()
        cls.alice = User.objects.create_user(email='alice74@test.com', password='pw', first_name='Alice')
        cls.bob = User.objects.create_user(email='bob74@test.com', password='pw', first_name='Bob')
        cls.order = Order.objects.create(
            user=cls.alice, status=Order.Status.PROCESSING,
            total_price=Decimal('79.99'), shipping_address='123 Secret St, Apt 4',
        )
        OrderItem.objects.create(
            order=cls.order, product=cls.headphones,
            product_name='Wireless Headphones', price=Decimal('79.99'), quantity=1,
        )

    @patch('assistant.views.ollama_client.chat', return_value='SHOULD NOT CALL')
    def test_anonymous_is_asked_to_log_in(self, mock_chat):
        res = self.client.post(self.url, {'message': 'Where is my order?'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['intent'], 'order_status')
        self.assertIn('sign in', res.data['reply'].lower())
        mock_chat.assert_not_called()          # no LLM, no DB leak

    @patch('assistant.views.ollama_client.chat', return_value='SHOULD NOT CALL')
    def test_authenticated_user_gets_own_latest_order(self, mock_chat):
        self.client.force_authenticate(user=self.alice)
        res = self.client.post(self.url, {'message': "What's the status of my latest order?"}, format='json')
        self.assertEqual(res.data['intent'], 'order_status')
        self.assertIn(self.order.order_number, res.data['reply'])
        self.assertIn('Processing', res.data['reply'])
        mock_chat.assert_not_called()
        self.assertNotIn('Secret St', res.data['reply'])   # privacy: no address

    def test_authenticated_user_gets_order_by_number(self):
        self.client.force_authenticate(user=self.alice)
        res = self.client.post(self.url, {'message': f'status of order {self.order.order_number}'}, format='json')
        self.assertIn(self.order.order_number, res.data['reply'])
        self.assertIn('Processing', res.data['reply'])

    def test_cross_user_access_is_denied(self):
        # Bob asks about Alice's order number -> not found (scoped to request.user).
        self.client.force_authenticate(user=self.bob)
        res = self.client.post(self.url, {'message': f'status of order {self.order.order_number}'}, format='json')
        self.assertEqual(res.data['intent'], 'order_status')
        self.assertNotIn(self.order.order_number, res.data['reply'])
        self.assertIn("couldn't find", res.data['reply'].lower())

    def test_user_with_no_orders(self):
        self.client.force_authenticate(user=self.bob)
        res = self.client.post(self.url, {'message': 'my latest order'}, format='json')
        self.assertIn("don't see any orders", res.data['reply'].lower())

    def test_invalid_order_number(self):
        self.client.force_authenticate(user=self.alice)
        res = self.client.post(self.url, {'message': 'status of order ORD-FAKE-9999'}, format='json')
        self.assertIn("couldn't find", res.data['reply'].lower())


class ChatEndpointTests(AssistantTestData):
    url = '/api/assistant/chat/'

    @patch('assistant.views.ollama_client.chat', return_value='I recommend the Wireless Headphones at $79.99.')
    def test_recommendation_endpoint_grounds_real_products(self, mock_chat):
        res = self.client.post(self.url, {'message': 'Recommend electronics under $100'}, format='json')
        self.assertEqual(res.data['intent'], 'recommendation')
        names = [p['name'] for p in res.data['products']]
        self.assertIn('Wireless Headphones', names)
        self.assertNotIn('Gaming Laptop', names)
        # Only in-stock, available products ever surface.
        self.assertTrue(all(p['is_available'] and p['stock'] > 0 for p in res.data['products']))
        system_content = mock_chat.call_args.args[0][0]['content']
        self.assertIn('79.99', system_content)

    @patch('assistant.views.ollama_client.chat', return_value='SHOULD NOT BE CALLED')
    def test_recommendation_no_match_is_deterministic(self, mock_chat):
        res = self.client.post(self.url, {'message': 'Recommend electronics under $5'}, format='json')
        self.assertEqual(res.data['intent'], 'recommendation')
        self.assertEqual(res.data['products'], [])
        mock_chat.assert_not_called()
        self.assertIn("couldn't find", res.data['reply'].lower())

    @patch('assistant.views.ollama_client.chat', return_value='Sure, happy to help!')
    def test_successful_reply(self, mock_chat):
        res = self.client.post(self.url, {'message': 'hello'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data['degraded'])
        self.assertEqual(res.data['intent'], 'general')

    @patch('assistant.views.ollama_client.chat', side_effect=OllamaError('down'))
    def test_graceful_fallback(self, _m):
        res = self.client.post(self.url, {'message': 'hello'}, format='json')
        self.assertEqual(res.status_code, 200)   # never a 500
        self.assertTrue(res.data['degraded'])
        self.assertIn('temporarily unavailable', res.data['reply'])

    @patch('assistant.views.ollama_client.chat', return_value='The Gaming Laptop is $1299.00.')
    def test_product_question_grounds_prompt_with_real_data(self, mock_chat):
        res = self.client.post(self.url, {'message': 'How much is the Gaming Laptop?'}, format='json')
        self.assertEqual(res.data['intent'], 'product')
        # Authoritative product data returned from the DB (not the LLM).
        names = [p['name'] for p in res.data['products']]
        self.assertIn('Gaming Laptop', names)
        laptop = next(p for p in res.data['products'] if p['name'] == 'Gaming Laptop')
        self.assertEqual(laptop['price'], '1299.00')
        self.assertEqual(laptop['stock'], 8)
        # The exact price/stock were injected into the prompt sent to Ollama.
        system_content = mock_chat.call_args.args[0][0]['content']
        self.assertIn('Gaming Laptop', system_content)
        self.assertIn('1299.00', system_content)
        self.assertIn('8 in stock', system_content)

    @patch('assistant.views.ollama_client.chat', return_value='You can return within 30 days.')
    def test_faq_question_grounds_prompt_with_faq_answer(self, mock_chat):
        res = self.client.post(self.url, {'message': 'What is your return policy?'}, format='json')
        self.assertEqual(res.data['intent'], 'faq')
        system_content = mock_chat.call_args.args[0][0]['content']
        self.assertIn('30 days', system_content)

    @patch('assistant.views.ollama_client.chat', return_value='SHOULD NOT BE CALLED')
    def test_unstocked_product_is_deterministic_and_skips_llm(self, mock_chat):
        # item 8 guarantee: no catalog match -> deterministic reply, LLM NOT called,
        # so the assistant can never invent a product we don't carry.
        res = self.client.post(self.url, {'message': 'Do you sell refrigerators?'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['intent'], 'product')
        self.assertEqual(res.data['products'], [])
        mock_chat.assert_not_called()
        self.assertNotIn('refrigerator', res.data['reply'].lower())
        self.assertIn("couldn't find", res.data['reply'].lower())

    def test_empty_message_rejected(self):
        res = self.client.post(self.url, {'message': '   '}, format='json')
        self.assertEqual(res.status_code, 400)
