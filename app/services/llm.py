"""Abstraction over the text-generation backend used for phrasing.

This is the dependency-inversion seam for the services layer: business logic
depends on the ``LLMClient`` interface defined here, never on a concrete
Gemini call. That keeps the phrasing backend swappable — real Gemini, a test
double, or a future offline fallback — without touching routing, crowd, or
facility logic.
"""
from abc import ABC, abstractmethod

from app.config import Settings
from app.services import gemini


class LLMClient(ABC):
    """Abstraction over any text-generation backend used for phrasing.

    Implementations only translate already-resolved facts into natural
    language — they must never be the source of truth for facts, routes, or
    facility data. This keeps the LLM swappable (real Gemini, a mock for
    tests, or a future offline fallback) without touching business logic in
    the services layer.
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Return generated text for the given prompt."""


class GeminiClient(LLMClient):
    """Concrete LLMClient backed by :func:`app.services.gemini.ask_gemini`.

    The ``gemini`` module is referenced (rather than importing ``ask_gemini``
    by name) so the call resolves the ``app.services.gemini.ask_gemini``
    attribute at call time — the single source of the real Gemini call, which
    keeps it substitutable in tests through one well-known seam.
    """

    async def generate(self, prompt: str) -> str:
        """Phrase ``prompt`` via the live Gemini call, propagating its errors."""
        return await gemini.ask_gemini(prompt)


def get_llm_client(settings: Settings) -> LLMClient:
    """Return the LLMClient appropriate for the given settings.

    This is the single place that decides which concrete implementation the
    app runs against, so wiring in ``create_app`` depends only on the
    ``LLMClient`` abstraction. It currently always returns the live
    Gemini-backed client; ``settings`` is the seam through which an offline
    implementation is selected when no API key is configured.
    """
    return GeminiClient()
