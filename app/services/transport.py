"""Light-touch AI-generated shuttle/transit suggestion based on distance to the venue."""
from app.services.gemini import ask_gemini

_LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "ar": "Arabic",
    "de": "German",
    "ja": "Japanese",
    "zh": "Mandarin Chinese",
}


async def suggest_transport(distance_km: float, language: str) -> str:
    """Ask Gemini for a brief transit/shuttle suggestion based on distance to the venue."""
    language_name = _LANGUAGE_NAMES.get(language, "English")
    prompt = (
        f"A fan is {distance_km:.1f} km from the stadium on match day. In {language_name}, "
        f"in under 50 words, suggest the most sensible way to get there (shuttle, transit, rideshare, "
        f"or walking) considering typical match-day traffic and sustainability."
    )
    return await ask_gemini(prompt)
