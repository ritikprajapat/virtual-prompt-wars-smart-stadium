"""Server-side wrapper around the Gemini API. The API key never leaves this process."""
import asyncio
import logging
from functools import lru_cache

from google import genai

from app.config import get_settings

logger = logging.getLogger(__name__)

_MODEL_NAME = "gemini-2.0-flash"
_TIMEOUT_SECONDS = 10


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
    try:
        client = _get_client()
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.models.generate_content, model=_MODEL_NAME, contents=prompt
            ),
            timeout=_TIMEOUT_SECONDS,
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
