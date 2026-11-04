"""
Thin HTTP client for the local Ollama server.

Django talks to Ollama here (server-side only) — the browser never contacts
Ollama directly. Everything raises `OllamaError` on failure so callers can show
a graceful fallback instead of a 500.

Ollama chat API:  POST {OLLAMA_BASE_URL}/api/chat
    body:  { "model": ..., "messages": [{"role","content"}, ...], "stream": false }
    reply: { "message": {"role":"assistant","content": "..."}, ... }
"""

import requests
from django.conf import settings

# How long we wait for the model to respond. CPU inference of a small model is
# usually a few seconds; we allow headroom but cap it so requests don't hang.
DEFAULT_TIMEOUT = 60


class OllamaError(Exception):
    """Raised when the Ollama server is unreachable or returns an error."""


def chat(messages, model=None, timeout=DEFAULT_TIMEOUT, options=None):
    """Send a chat completion request and return the assistant's text reply.

    `messages` is a list of {"role": "system"|"user"|"assistant", "content": str}.
    Raises OllamaError on any network/HTTP/parse problem.
    """
    model = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
    payload = {"model": model, "messages": messages, "stream": False}
    if options:
        payload["options"] = options

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    except (requests.exceptions.RequestException, KeyError, ValueError) as exc:
        raise OllamaError(str(exc)) from exc


def is_available(timeout=3):
    """Quick health probe — True if the Ollama server responds to /api/tags."""
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False
