"""Rate limiting for AI-calling routes, backed by slowapi's in-memory limiter."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


def ai_rate_limit() -> str:
    """Rate limit string (e.g. '20/minute') derived from settings, for use in decorators."""
    return f"{get_settings().rate_limit_per_minute}/minute"
