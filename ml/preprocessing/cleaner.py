"""Text Preprocessing Module for Kollamo.ai.

Safe, reproducible text normalization for Malayalam script, Manglish,
English, and Malayalam-English code-mixed comments.
Adheres strictly to AGENTS.md: NO sentiment dictionaries, NO keyword scoring.
"""

import re
import unicodedata
from typing import Tuple


def normalize_unicode(text: str) -> str:
    """Normalize text using Unicode NFKC normalization.

    Ensures consistent representation of Malayalam vowels, chillu characters,
    and Latin diacritics.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFKC", text)


def remove_urls(text: str) -> str:
    """Remove URLs (http, https, www) while preserving surrounding text."""
    pattern = r"https?://\S+|www\.\S+"
    return re.sub(pattern, "", text)


def remove_user_mentions(text: str) -> str:
    """Remove user handles/mentions (@username) common in social comments."""
    pattern = r"@[\w\.-]+"
    return re.sub(pattern, "", text)


def normalize_repeated_characters(text: str, max_repeat: int = 2) -> str:
    """Reduce prolonged repeated characters to at most `max_repeat` occurrences.

    Example:
        'poliiiiii' -> 'polii'
        'superrrrr' -> 'superr'
        'പൊളളളളളളി' -> 'പൊള്ളി'
    """
    pattern = re.compile(r"(.)\1{" + str(max_repeat) + r",}", re.UNICODE)
    return pattern.sub(r"\1" * max_repeat, text)


def normalize_whitespace(text: str) -> str:
    """Collapse consecutive whitespaces, tabs, and newlines into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def sanitize_control_characters(text: str) -> str:
    """Remove invisible non-printable control characters.

    Preserves Malayalam zero-width joiners (ZWJ: \\u200D) and non-joiners (ZWNJ: \\u200C)
    which are required for authentic Malayalam chillu characters and conjuncts.
    """
    cleaned_chars = []
    for ch in text:
        # Keep ZWJ (\u200D) and ZWNJ (\u200C) for Malayalam script validity
        if ch in ("\u200C", "\u200D"):
            cleaned_chars.append(ch)
        elif unicodedata.category(ch)[0] != "C":
            cleaned_chars.append(ch)
    return "".join(cleaned_chars)


def clean_text(text: str, max_chars: int = None) -> str:
    """Full preprocessing pipeline for Malayalam and code-mixed comments.

    Pipeline:
    1. Null / type check
    2. Optional length capping
    3. Unicode NFKC normalization
    4. URL removal
    5. User mention removal
    6. Control character sanitization
    7. Repeated character normalization (max 2)
    8. Whitespace collapse
    """
    if not text or not isinstance(text, str):
        return ""

    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars]

    text = normalize_unicode(text)
    text = remove_urls(text)
    text = remove_user_mentions(text)
    text = sanitize_control_characters(text)
    text = normalize_repeated_characters(text, max_repeat=2)
    text = normalize_whitespace(text)

    return text


def preprocess_comment(raw_text: str) -> Tuple[str, str]:
    """Processes a comment while preserving the raw text for display.

    Returns:
        (original_text, cleaned_text)
    """
    cleaned = clean_text(raw_text)
    return raw_text, cleaned
