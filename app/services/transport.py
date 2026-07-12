"""AI-phrased shuttle/transit suggestion based on distance to the venue."""
from app.services.gemini import ask_gemini
from app.services.i18n import language_name


async def suggest_transport(distance_km: float, language: str) -> str:
    """Ask Gemini for a brief transit suggestion based on distance to the venue."""
    lang_name = language_name(language)
    prompt = (
        f"A fan is {distance_km:.1f} km from the stadium on match day. In {lang_name}, "
        f"in under 50 words, suggest the most sensible way to get there "
        f"(shuttle, transit, "
        f"rideshare, or walking) considering typical match-day traffic "
        f"and sustainability."
    )
    return await ask_gemini(prompt)
