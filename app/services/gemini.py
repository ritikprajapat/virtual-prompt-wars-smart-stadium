"""Server-side wrapper around the Gemini API. The API key never leaves this process.

Gemini is used only as a phrasing layer over facts the deterministic services
have already computed, so it is confined to this one module behind
``ask_gemini``. Every failure — missing key, timeout, or API error — is caught
and re-raised as a generic ``RuntimeError`` with a log-safe message, so callers
fail closed (routes translate it to a 502) and no provider detail or raw
exception ever reaches a client.
"""
import asyncio
import logging
from functools import lru_cache

from google import genai

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _get_client() -> genai.Client:
    """Build (and cache) the Gemini client, raising if no API key is configured."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=settings.gemini_api_key)


async def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return plain text.

    Raises RuntimeError on any failure (missing key, timeout, API error) with a
    message safe to log server-side. Callers should catch this and return a
    generic error to the client rather than the raw exception.
    """
    settings = get_settings()
    try:
        client = _get_client()
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model,
                contents=prompt,
            ),
            timeout=settings.gemini_timeout_seconds,
        )
        text: str | None = getattr(response, "text", None)
        if not text:
            raise RuntimeError("empty response from Gemini")
        return text.strip()
    except TimeoutError as exc:
        logger.warning("Gemini request timed out")
        raise RuntimeError("AI request timed out") from exc
    except Exception as exc:
        logger.warning("Gemini request failed: %s", exc)
        raise RuntimeError("AI request failed") from exc
