"""Script and Language Identification for Malayalam, Manglish, and Code-Mixed text."""

import re
from typing import Dict, Tuple

MALAYALAM_UNICODE_RANGE = re.compile(r"[\u0D00-\u0D7F]")
LATIN_ALPHABET_RANGE = re.compile(r"[a-zA-Z]")

# Common Manglish phonetic suffixes & discourse particles
MANGLISH_MARKERS = {
    "aayirunnu", "aayi", "aanu", "alla", "illa", "undu", "polichu", "kidilan",
    "padam", "pakshe", "enthoru", "super", "mass", "chali", "thara", "kandu",
    "chettan", "nalla", "mosham", "adipoli", "level", "scene", "theerumanam"
}


def detect_script(text: str) -> str:
    """Identifies the script used in the comment.

    Returns:
        'Malayalam' | 'Latin' | 'Mixed' | 'Unknown'
    """
    if not text:
        return "Unknown"

    has_malayalam = bool(MALAYALAM_UNICODE_RANGE.search(text))
    has_latin = bool(LATIN_ALPHABET_RANGE.search(text))

    if has_malayalam and has_latin:
        return "Mixed"
    if has_malayalam:
        return "Malayalam"
    if has_latin:
        return "Latin"
    return "Unknown"


def detect_language(text: str) -> str:
    """Classifies the language representation into:
    - 'ml': Pure Malayalam script
    - 'ml-en': Code-mixed or Manglish (Romanized Malayalam)
    - 'en': Pure standard English
    - 'unknown': Numbers, punctuation, or unsupported script
    """
    if not text:
        return "unknown"

    script = detect_script(text)

    if script == "Malayalam":
        return "ml"

    if script == "Mixed":
        return "ml-en"

    if script == "Latin":
        # Check if Latin text contains Manglish vocabulary
        tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        manglish_overlap = tokens.intersection(MANGLISH_MARKERS)
        if manglish_overlap:
            return "ml-en"
        # If Latin without Manglish markers, check token length & vocabulary
        return "en"

    return "unknown"


def analyze_script_and_language(text: str) -> Dict[str, str]:
    """Returns detected script and language codes."""
    return {
        "script": detect_script(text),
        "language": detect_language(text),
    }
