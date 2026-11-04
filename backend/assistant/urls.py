"""
URL routes for the assistant app, mounted under /api/assistant/ by config/urls.

    POST /api/assistant/chat/     -> send a message, get an AI reply
    GET  /api/assistant/health/   -> is the Ollama backend reachable?
"""

from django.urls import path

from .views import ChatView, HealthView, RecommendationsView

urlpatterns = [
    path('chat/', ChatView.as_view(), name='assistant-chat'),
    path('recommendations/', RecommendationsView.as_view(), name='assistant-recommendations'),
    path('health/', HealthView.as_view(), name='assistant-health'),
]
