"""
Models for the assistant app.

FAQ holds canned question/answer pairs the assistant uses to answer common
support questions accurately (no LLM invention). `keywords` is an optional
comma-separated list that helps the rule-based matcher.

(Persistent chat history is deferred to an optional later subphase.)
"""

from django.db import models


class FAQ(models.Model):
    """A frequently-asked question and its authoritative answer."""

    question = models.CharField(max_length=255, unique=True)
    answer = models.TextField()
    # Comma-separated terms to improve matching, e.g. "shipping,delivery,ship".
    keywords = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ('question',)

    def keyword_list(self):
        """Return keywords as a lowercased list (plus words from the question)."""
        parts = [k.strip().lower() for k in self.keywords.split(',') if k.strip()]
        return parts

    def __str__(self):
        return self.question
