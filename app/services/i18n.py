"""Shared internationalization helpers for the AI-phrasing services.

Keeping the language table in one place avoids duplicating it across every
service that asks Gemini for user-facing text in the guest's language.
"""

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


def language_name(code: str) -> str:
    """Return the human-readable language name for an ISO 639-1 code.

    Falls back to "English" for any unknown or unsupported code.
    """
    return _LANGUAGE_NAMES.get(code, "English")
