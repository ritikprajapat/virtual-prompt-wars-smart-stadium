"""Abstraction over the text-generation backend used for phrasing.

This is the dependency-inversion seam for the services layer: business logic
depends on the ``LLMClient`` interface defined here, never on a concrete
Gemini call. That keeps the phrasing backend swappable — real Gemini, a test
double, or a future offline fallback — without touching routing, crowd, or
facility logic.
"""
from abc import ABC, abstractmethod


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

    ``ask_gemini`` is imported lazily inside :meth:`generate` so this module
    stays free of the Gemini SDK import chain and the single source of the
    real call can be substituted in tests via the one ``app.services.gemini``
    module attribute.
    """

    async def generate(self, prompt: str) -> str:
        """Phrase ``prompt`` via the live Gemini call, propagating its errors."""
        from app.services.gemini import ask_gemini

        return await ask_gemini(prompt)
