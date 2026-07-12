"""Tests for the shared i18n language-name resolution."""
import pytest

from app.models.requests import Language
from app.services.i18n import language_name

_EXPECTED = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "pt": "Portuguese",
    "ar": "Arabic",
    "de": "German",
    "ja": "Japanese",
    "zh": "Mandarin Chinese",
}


@pytest.mark.parametrize("code,name", list(_EXPECTED.items()))
def test_every_supported_code_resolves(code, name):
    assert language_name(code) == name


def test_every_language_enum_value_is_supported():
    # Guards against a Language enum member without a matching name entry.
    for language in Language:
        assert language_name(language.value) != "English" or language is Language.EN


@pytest.mark.parametrize("code", ["", "xx", "klingon", "EN", "zz", "en-US"])
def test_unknown_code_falls_back_to_english(code):
    assert language_name(code) == "English"
