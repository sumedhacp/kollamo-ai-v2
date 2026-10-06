"""Unit Tests for Text Preprocessing and Script/Language Detection."""

import pytest
from ml.preprocessing.cleaner import (
    normalize_unicode,
    remove_urls,
    remove_user_mentions,
    normalize_repeated_characters,
    normalize_whitespace,
    clean_text,
    preprocess_comment,
)
from ml.preprocessing.detector import detect_script, detect_language, analyze_script_and_language


def test_remove_urls():
    text = "Check this trailer https://youtube.com/watch?v=12345 super movie!"
    cleaned = remove_urls(text)
    assert "https://" not in cleaned
    assert "super movie!" in cleaned


def test_remove_mentions():
    text = "Great work by @actor_name and @director!"
    cleaned = remove_user_mentions(text)
    assert "@actor_name" not in cleaned
    assert "Great work" in cleaned


def test_normalize_repeated_characters():
    assert normalize_repeated_characters("poliiiiiii") == "polii"
    assert normalize_repeated_characters("superrrrrrr") == "superr"
    assert normalize_repeated_characters("പൊളളളളളളി") == "പൊളളി"


def test_clean_text_preserves_malayalam_script():
    malayalam_text = "തിയേറ്ററിൽ തന്നെ കാണണം @friend https://link.com poliiii!"
    cleaned = clean_text(malayalam_text)
    assert "തിയേറ്ററിൽ തന്നെ കാണണം" in cleaned
    assert "polii!" in cleaned
    assert "https://" not in cleaned
    assert "@friend" not in cleaned


def test_preprocess_comment_preserves_original():
    raw = "  Superrrr padam https://link.com  "
    orig, cleaned = preprocess_comment(raw)
    assert orig == raw
    assert cleaned == "Superr padam"


def test_detect_script():
    assert detect_script("മലയാളം") == "Malayalam"
    assert detect_script("Padam kidilan aayirunnu") == "Latin"
    assert detect_script("Climax scene ഗംഭീരം aayirunnu") == "Mixed"
    assert detect_script("12345 !@#$") == "Unknown"


def test_detect_language():
    assert detect_language("ഈ പടം കൊള്ളാം") == "ml"
    assert detect_language("Padam kidilan aayirunnu") == "ml-en"  # Manglish
    assert detect_language("Climax scene ഗംഭീരം") == "ml-en"       # Code-mixed
    assert detect_language("Outstanding performance by the entire cast") == "en"  # English
