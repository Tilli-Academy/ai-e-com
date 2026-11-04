"""
Prompt assembly for the assistant.

The system prompt forbids inventing facts; real data (FAQ answers, product
records) is injected as CONTEXT so the model only phrases authoritative info.
"""

SYSTEM_PROMPT = (
    "You are ShopAI's friendly shopping assistant for an online store. "
    "Be concise, warm, and helpful.\n\n"
    "IMPORTANT GROUNDING RULES:\n"
    "- Only use the information in the CONTEXT section below.\n"
    "- Never invent products, prices, stock levels, or policies.\n"
    "- If the CONTEXT does not contain the answer, say you don't have that "
    "information and suggest browsing the catalog — do not guess.\n"
    "- When mentioning a product, use its exact name and price from the CONTEXT."
)

# Shown when the LLM backend is unreachable, so the user never sees a raw error.
FALLBACK_MESSAGE = (
    "Sorry — the shopping assistant is temporarily unavailable. "
    "Please try again in a moment."
)

# Deterministic reply used when a product question matches NOTHING in the catalog.
# We return this WITHOUT calling the LLM, guaranteeing the assistant never claims
# we sell an item we don't actually carry.
NO_PRODUCT_MATCH_MESSAGE = (
    "I couldn't find that in our catalog, so it looks like we don't currently "
    "carry it. You can browse everything we stock on the Products page, or ask "
    "me about a specific item we sell."
)


# --- Order-status messages (deterministic; no LLM, for accuracy + privacy) ----

LOGIN_REQUIRED_MESSAGE = (
    "You'll need to sign in to check your order status. Please log in and ask "
    "me again, and I'll look it up for you."
)
NO_ORDERS_MESSAGE = (
    "I don't see any orders on your account yet. Once you place an order, I can "
    "tell you its status here."
)
NO_ORDER_NUMBER_MESSAGE = (
    "I couldn't find an order with that number on your account. Please "
    "double-check it in \"My Orders\"."
)


def order_status_reply(order):
    """Deterministic, factual order summary built straight from the DB.

    Intentionally omits the shipping address and any other personal details —
    we only report status, date, items, and total."""
    date = order.created_at.strftime('%b %d, %Y')
    items = ', '.join(
        f'{it.quantity}x {it.product_name}' for it in order.items.all()
    )
    return (
        f"Your order {order.order_number} (placed {date}) is currently "
        f"\"{order.get_status_display()}\". "
        f"It includes: {items}. Total: ${order.total_price}."
    )


def no_recommendation_message(criteria):
    """Deterministic reply when a recommendation request matches no products.
    Tailored with the parsed category/budget. Returned WITHOUT the LLM so no
    product is ever invented."""
    category = criteria.get('category')
    max_price = criteria.get('max_price')
    bits = []
    if category:
        bits.append(f'{category.name.lower()}')
    if max_price is not None:
        bits.append(f'under ${max_price}')
    criteria_text = ' '.join(bits)
    if criteria_text:
        return (
            f"I couldn't find any in-stock {criteria_text} right now. "
            "Try a higher budget or a different category, or browse all our "
            "products on the Products page."
        )
    return (
        "I couldn't find anything in stock to recommend right now. "
        "Please browse our Products page to see what's available."
    )


def build_product_context(products):
    """Authoritative product lines for the prompt (exact name/price/stock)."""
    if not products:
        return ''
    lines = ['Products in our catalog that may be relevant:']
    for p in products:
        stock = f'{p.stock} in stock' if p.stock > 0 else 'out of stock'
        lines.append(
            f'- {p.name} (category: {p.category.name}): '
            f'${p.price}, {stock}.'
        )
    return '\n'.join(lines)


def build_faq_context(faqs):
    """Authoritative FAQ Q&A lines for the prompt."""
    if not faqs:
        return ''
    lines = ['Relevant store FAQs:']
    for f in faqs:
        lines.append(f'Q: {f.question}\nA: {f.answer}')
    return '\n'.join(lines)


def build_chat_messages(message, intent_data):
    """Assemble the messages list sent to Ollama, grounded on real data."""
    intent = intent_data.get('intent')
    faqs = intent_data.get('faqs')
    products = intent_data.get('products')

    context_blocks = []
    faq_ctx = build_faq_context(faqs)
    product_ctx = build_product_context(products)
    if faq_ctx:
        context_blocks.append(faq_ctx)
    if product_ctx:
        context_blocks.append(product_ctx)

    # For a recommendation, tell the model to suggest only from the listed items.
    if intent == 'recommendation' and product_ctx:
        context_blocks.append(
            'The customer wants a recommendation. Suggest ONLY from the products '
            'listed above, mentioning each item\'s exact name, price, and that '
            'it is in stock. Do not invent other products.'
        )

    if context_blocks:
        context = 'CONTEXT:\n' + '\n\n'.join(context_blocks)
    elif intent == 'product':
        # A product-style question with NO catalog match: be explicit so the
        # model does not invent a product. (item 8 guarantee)
        context = (
            'CONTEXT:\n'
            'No products in our catalog match this request. We do NOT carry this '
            'item. Tell the customer we currently do not stock it and suggest '
            'they browse our available products. Do NOT describe, list, or invent '
            'any such product, price, or specification.'
        )
    else:
        context = ('CONTEXT:\n(No specific catalog or FAQ data matched. Answer '
                   'general shopping questions only; do not invent specifics.)')

    system = f'{SYSTEM_PROMPT}\n\n{context}'
    return [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': message},
    ]
