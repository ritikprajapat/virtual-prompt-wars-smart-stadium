"""Shared HTTP error helpers used across API routes."""
from fastapi import HTTPException


def ai_service_unavailable() -> HTTPException:
    """Build the standard 502 raised when an AI (Gemini) call fails.

    Use as ``raise ai_service_unavailable() from exc`` so the underlying
    cause is preserved in the traceback while clients see a generic message.
    """
    return HTTPException(
        status_code=502,
        detail="AI service unavailable, please try again",
    )
