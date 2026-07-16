"""AI-phrased shuttle/transit suggestion based on distance to the venue.

The AI call is injected via the LLMClient abstraction (app.services.llm)
rather than called directly, so phrasing can be swapped, mocked, or replaced
with an offline fallback without changing business logic here.
"""
from app.services.i18n import language_name
from app.services.llm import GeminiClient, LLMClient

_default_llm: LLMClient = GeminiClient()


async def suggest_transport(
    distance_km: float, language: str, llm: LLMClient | None = None
) -> str:
    """Ask the LLM for a brief transit suggestion based on distance to the venue."""
    lang_name = language_name(language)
    prompt = (
        f"A fan is {distance_km:.1f} km from the stadium on match day. In {lang_name}, "
        f"in under 50 words, suggest the most sensible way to get there "
        f"(shuttle, transit, "
        f"rideshare, or walking) considering typical match-day traffic "
        f"and sustainability."
    )
    return await (llm or _default_llm).generate(prompt)
