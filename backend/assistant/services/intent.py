"""
Rule-based intent detection + grounding lookups for the assistant.

Deterministic (no LLM): we classify the message and fetch the REAL records the
answer must be grounded on. Order-status intent is added in 7.4.

Intents: 'faq' | 'product' | 'general'
"""

import re
from decimal import Decimal, InvalidOperation

from products.models import Category, Product

from assistant.models import FAQ

# Phrases/words that signal a question about a SPECIFIC catalog item.
PRODUCT_SIGNALS = {
    'price', 'cost', 'how much', 'stock', 'available', 'availability',
    'in stock', 'do you have', 'do you sell', 'buy', 'sell', 'product',
    'products', 'catalog',
}

# Phrases/words that signal a request for RECOMMENDATIONS (checked before the
# specific-product signals above).
RECOMMENDATION_SIGNALS = {
    'recommend', 'recommendation', 'suggest', 'suggestion', 'show me', 'show',
    'cheapest', 'best', 'under', 'below', 'less than', 'looking for', 'options',
    'budget', 'what should i buy',
}

# Order number like ORD-20261104-7F3A9C (case-insensitive).
ORDER_NUMBER_RE = re.compile(r'ORD-[A-Za-z0-9-]+', re.IGNORECASE)

# Phrases asking about the user's OWN order status. Deliberately does NOT
# include "track my order" so the how-to FAQ "How do I track my order?" keeps
# routing to the FAQ table.
ORDER_STATUS_PHRASES = {
    'my latest order', 'my last order', 'my recent order', 'latest order',
    'status of my order', 'status of order', 'where is my order',
    "where's my order", 'my order status', 'how is my order', 'order update',
}


def extract_order_number(message):
    """Return an ORD-... order number found in the message (upper-cased), or None.
    This is only a lookup KEY — ownership is always enforced against the
    authenticated user in the view."""
    match = ORDER_NUMBER_RE.search(message)
    return match.group(0).upper() if match else None


def is_order_status_query(message):
    """True if the message asks about the user's own order status."""
    if extract_order_number(message):
        return True
    msg = message.lower()
    return any(phrase in msg for phrase in ORDER_STATUS_PHRASES)

_WORD_RE = re.compile(r"[a-z0-9]+")

# Common words that carry no matching signal — excluded so overlaps are meaningful
# (prevents e.g. "do"/"you"/"the" from spuriously matching FAQs or products).
_STOPWORDS = {
    'do', 'you', 'i', 'is', 'are', 'am', 'the', 'a', 'an', 'to', 'of', 'in', 'on',
    'for', 'and', 'or', 'my', 'me', 'your', 'we', 'it', 'this', 'that', 'these',
    'how', 'what', 'where', 'when', 'which', 'who', 'can', 'could', 'would',
    'should', 'will', 'have', 'has', 'had', 'need', 'want', 'with', 'about',
    'please', 'hi', 'hello', 'hey', 'there', 'any', 'some', 'get', 'tell',
}


def _tokens(text):
    return {t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS}


def match_faqs(message, limit=3):
    """Return FAQs relevant to the message, best first (by keyword/question
    token overlap). Empty if nothing meaningfully matches."""
    msg = message.lower()
    msg_tokens = _tokens(message)
    scored = []
    for faq in FAQ.objects.filter(is_active=True):
        score = 0
        # Phrase keywords (e.g. "how long") get a strong boost on substring hit.
        for kw in faq.keyword_list():
            if kw and kw in msg:
                score += 2 if ' ' in kw else 1
        # Token overlap with the question itself.
        score += len(msg_tokens & _tokens(faq.question))
        if score > 0:
            scored.append((score, faq))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [faq for _, faq in scored[:limit]]


def search_products(message, limit=5):
    """Return AVAILABLE products relevant to the message.

    Matches product name/description tokens and category names. Only
    is_available=True products are ever surfaced (same visibility rule as the
    public catalog)."""
    msg = message.lower()
    msg_tokens = _tokens(message)
    if not msg_tokens:
        return []

    qs = Product.objects.filter(is_available=True).select_related('category')

    # Category mentioned by name -> include that category's products.
    category_ids = [
        c.id for c in Category.objects.all() if c.name.lower() in msg
    ]

    scored = []
    for p in qs:
        score = 0
        name_tokens = _tokens(p.name)
        score += 3 * len(msg_tokens & name_tokens)          # name match is strong
        score += len(msg_tokens & _tokens(p.description))   # description match
        if p.category_id in category_ids:
            score += 2
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [p for _, p in scored[:limit]]


# ---------------------------------------------------------------------------
# Recommendations (7.3)
# ---------------------------------------------------------------------------

# "under 100", "below $40", "less than 50", "up to 30", "$100"
_PRICE_LIMIT_RE = re.compile(
    r'(?:under|below|less than|up to|max(?:imum)?|cheaper than|<)\s*\$?\s*(\d+(?:\.\d+)?)'
)
_PRICE_ANY_RE = re.compile(r'\$\s*(\d+(?:\.\d+)?)')


def extract_max_price(message):
    """Return the maximum budget mentioned in the message, or None."""
    msg = message.lower()
    match = _PRICE_LIMIT_RE.search(msg) or _PRICE_ANY_RE.search(msg)
    if not match:
        return None
    try:
        return Decimal(match.group(1))
    except InvalidOperation:
        return None


def extract_category(message):
    """Return a Category mentioned in the message (by name or significant word)."""
    msg = message.lower()
    for category in Category.objects.all():
        name = category.name.lower()
        if name in msg:
            return category
        # e.g. "kitchen" should match "Home & Kitchen"
        words = [w for w in _WORD_RE.findall(name) if len(w) > 2 and w not in _STOPWORDS]
        if any(w in msg for w in words):
            return category
    return None


def recommend_products(message, limit=5):
    """Return in-stock, available products matching the request + the parsed
    criteria. Applies category and budget filters; narrows by product-name
    terms when present; otherwise returns the cheapest options."""
    category = extract_category(message)
    max_price = extract_max_price(message)

    qs = Product.objects.filter(is_available=True, stock__gt=0).select_related('category')
    if category:
        qs = qs.filter(category=category)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)

    msg_tokens = _tokens(message)
    scored = []
    any_name_match = False
    for p in qs:
        score = 3 * len(msg_tokens & _tokens(p.name)) + len(msg_tokens & _tokens(p.description))
        scored.append((score, p))
        if score > 0:
            any_name_match = True

    if any_name_match:
        scored = [s for s in scored if s[0] > 0]
        scored.sort(key=lambda s: (-s[0], s[1].price))
    else:
        # No specific item named -> recommend the cheapest matching options.
        scored.sort(key=lambda s: s[1].price)

    products = [p for _, p in scored[:limit]]
    return products, {'category': category, 'max_price': max_price}


def detect_intent(message):
    """Classify the message and return the grounding data.

    Returns { 'intent', 'faqs', 'products', 'criteria' }.

    Priority: order_status -> faq -> recommendation -> product -> general.
    """
    msg = message.lower()

    # Order-status is checked first; the DB lookup (scoped to request.user)
    # happens in the view, never here, so ownership can't be bypassed.
    if is_order_status_query(message):
        return {'intent': 'order_status', 'faqs': [], 'products': [],
                'criteria': {}, 'order_number': extract_order_number(message)}

    faqs = match_faqs(message)
    if faqs:
        return {'intent': 'faq', 'faqs': faqs, 'products': [], 'criteria': {}}

    if any(sig in msg for sig in RECOMMENDATION_SIGNALS):
        products, criteria = recommend_products(message)
        return {'intent': 'recommendation', 'faqs': [], 'products': products,
                'criteria': criteria}

    has_product_signal = any(sig in msg for sig in PRODUCT_SIGNALS)
    products = search_products(message)
    if has_product_signal or products:
        return {'intent': 'product', 'faqs': [], 'products': products, 'criteria': {}}

    return {'intent': 'general', 'faqs': [], 'products': [], 'criteria': {}}
