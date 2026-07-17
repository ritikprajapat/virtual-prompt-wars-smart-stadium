"""Abstraction over the text-generation backend used for phrasing.

This is the dependency-inversion seam for the services layer: business logic
depends on the ``LLMClient`` interface defined here, never on a concrete
Gemini call. That keeps the phrasing backend swappable — real Gemini, a test
double, or a future offline fallback — without touching routing, crowd, or
facility logic.
"""
import logging
from abc import ABC, abstractmethod

from app.config import Settings, get_settings
from app.services import gemini

logger = logging.getLogger(__name__)

# Shown verbatim when the offline fallback is active. It intentionally names no
# specifics: the caller only hands us a prompt, not the underlying facts, so any
# structured data (route steps, facilities, impact rank) is still returned by the
# route alongside this phrasing — only the natural-language wording degrades.
_FALLBACK_MESSAGE = (
    "AI phrasing is temporarily unavailable, so detailed guidance can't be "
    "generated right now. The key details are shown above — please try again "
    "shortly for a full description."
)


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


class FallbackLLMClient(LLMClient):
    """Wraps another :class:`LLMClient` and degrades gracefully on failure.

    On success it is a transparent pass-through. When the wrapped client
    raises ``RuntimeError`` (the failure every backend normalises to), it logs
    the cause and returns a static message instead of propagating — so a
    Gemini outage downgrades wording rather than turning into a 502. This is a
    Decorator over the ``LLMClient`` seam, so it composes with any backend.
    """

    def __init__(self, inner: LLMClient, fallback: str = _FALLBACK_MESSAGE) -> None:
        """Wrap ``inner``, returning ``fallback`` text when it raises."""
        self._inner = inner
        self._fallback = fallback

    async def generate(self, prompt: str) -> str:
        """Delegate to the wrapped client, substituting fallback text on failure."""
        try:
            return await self._inner.generate(prompt)
        except RuntimeError as exc:
            logger.warning("LLM unavailable, using offline fallback: %s", exc)
            return self._fallback


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """Return the LLMClient the app runs against.

    This is the single place that decides which concrete implementation is
    wired in, so ``create_app`` depends only on the ``LLMClient`` abstraction
    and never names a concrete client itself. When ``llm_offline_fallback`` is
    enabled the live client is wrapped in :class:`FallbackLLMClient`; otherwise
    a raw :class:`GeminiClient` is returned and its failures surface as a 502.
    """
    settings = settings or get_settings()
    client: LLMClient = GeminiClient()
    if settings.llm_offline_fallback:
        client = FallbackLLMClient(client)
    return client
