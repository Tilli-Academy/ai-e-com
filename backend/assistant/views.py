"""
Views for the AI shopping assistant.

7.2: the chat endpoint now detects intent (FAQ / product / general), grounds the
prompt on REAL FAQ and product records, and returns the matched products
(authoritative, straight from the DB) alongside the LLM reply so the frontend
never depends on the model for product facts. Graceful Ollama fallback preserved.
Order-status grounding arrives in 7.4.
"""

from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from orders.models import Order
from products.serializers import ProductSerializer

from .prompts import (
    FALLBACK_MESSAGE,
    LOGIN_REQUIRED_MESSAGE,
    NO_ORDER_NUMBER_MESSAGE,
    NO_ORDERS_MESSAGE,
    NO_PRODUCT_MATCH_MESSAGE,
    build_chat_messages,
    no_recommendation_message,
    order_status_reply,
)
from .serializers import ChatRequestSerializer
from .services import intent as intent_service
from .services import ollama_client


def _product_payload(products):
    """Authoritative product data for the API response (from the DB, not the LLM)."""
    return [
        {
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price': str(p.price),
            'stock': p.stock,
            'is_available': p.is_available,
        }
        for p in products
    ]


class ChatView(APIView):
    """POST /api/assistant/chat/ — grounded AI reply for FAQ/product/general.

    Public + throttled. Ollama failure -> friendly fallback at HTTP 200.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'assistant'

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data['message']

        # 1) Rule-based intent + real grounding data (no LLM yet).
        intent_data = intent_service.detect_intent(message)

        # 1a) Order status: authenticated + user-scoped, answered deterministically.
        if intent_data['intent'] == 'order_status':
            return self._order_status_response(request, intent_data)

        # 2) Guarantee (no invention): a product OR recommendation request with
        #    NO catalog match is answered deterministically WITHOUT the LLM.
        if not intent_data['products']:
            if intent_data['intent'] == 'product':
                return Response({
                    'reply': NO_PRODUCT_MATCH_MESSAGE,
                    'degraded': False, 'intent': 'product', 'products': [],
                })
            if intent_data['intent'] == 'recommendation':
                return Response({
                    'reply': no_recommendation_message(intent_data.get('criteria', {})),
                    'degraded': False, 'intent': 'recommendation', 'products': [],
                })

        # 3) Otherwise build a grounded prompt and let the model phrase the answer.
        messages = build_chat_messages(message, intent_data)
        try:
            reply = ollama_client.chat(messages)
        except ollama_client.OllamaError:
            return Response({
                'reply': FALLBACK_MESSAGE,
                'degraded': True,
                'intent': intent_data['intent'],
                'products': _product_payload(intent_data['products']),
            })

        return Response({
            'reply': reply,
            'degraded': False,
            'intent': intent_data['intent'],
            # Authoritative product data (not from the LLM) for the frontend.
            'products': _product_payload(intent_data['products']),
        })

    def _order_status_response(self, request, intent_data):
        """Answer an order-status question securely.

        - Requires authentication (anonymous -> login message, no DB access).
        - Looks up orders ONLY for request.user (ownership from the token, never
          from the message), so another user's order number returns "not found".
        - Replies deterministically (no LLM) with status/date/items/total; the
          shipping address and other personal details are never included.
        """
        def payload(reply):
            return Response({'reply': reply, 'degraded': False,
                             'intent': 'order_status', 'products': []})

        if not request.user or not request.user.is_authenticated:
            return payload(LOGIN_REQUIRED_MESSAGE)

        orders = Order.objects.filter(user=request.user)   # user-scoped ownership
        order_number = intent_data.get('order_number')
        if order_number:
            order = orders.filter(order_number__iexact=order_number).first()
            if order is None:
                return payload(NO_ORDER_NUMBER_MESSAGE)
        else:
            order = orders.order_by('-created_at').first()   # the user's latest
            if order is None:
                return payload(NO_ORDERS_MESSAGE)

        return payload(order_status_reply(order))


class RecommendationsView(APIView):
    """GET /api/assistant/recommendations/ — products for the homepage
    "Recommended for You" section.

    Reuses the existing rule-based recommender (recommend_products) — no LLM —
    and serializes with the catalog's ProductSerializer so the response matches
    what the product grid already consumes. Out-of-stock/unavailable products
    are already excluded by recommend_products.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        products, _criteria = intent_service.recommend_products(query, limit=8)
        data = ProductSerializer(products, many=True, context={'request': request}).data
        return Response({'products': data})


class HealthView(APIView):
    """GET /api/assistant/health/ — is the LLM backend reachable? (diagnostics)"""

    permission_classes = [AllowAny]

    def get(self, request):
        up = ollama_client.is_available()
        return Response({
            'ollama': 'up' if up else 'down',
            'model': settings.OLLAMA_MODEL,
        })
