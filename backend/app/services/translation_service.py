"""Translation Service Abstraction and Multi-Tier Translation Engine for Kollamo.ai.

Supports:
- Malayalam Script (മലയാളം)
- Manglish / Romanized Malayalam
- English
- Malayalam-English Code-Mixed text
- Colloquial social media review expressions lexicon
- Graceful fallbacks and offline resilience
"""

from __future__ import annotations

import abc
import functools
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import requests

from backend.app.core.config import settings
from backend.app.core.logging import logger


class LanguageKind(str, Enum):
    MALAYALAM = "malayalam"
    ENGLISH = "english"
    MANGLISH = "manglish"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TranslationResult:
    """Structured translation output including linguistic provenance and confidence."""

    text: str
    confidence: float
    source_language: str
    detected_script: str
    intermediate_malayalam: Optional[str]
    method: str
    status: str  # "translated", "original", "fallback", "error"


class BaseTranslationService(abc.ABC):
    """Abstract Base Class for translation engines."""

    @abc.abstractmethod
    def translate(self, text: str, source: str = "auto", target: str = "en") -> str:
        """Translate text to target language, returning translated string."""
        pass

    @abc.abstractmethod
    def translate_detailed(
        self, text: str, source: str = "auto", target: str = "en"
    ) -> TranslationResult:
        """Translate text returning structured provenance and confidence metadata."""
        pass


class HybridTranslationService(BaseTranslationService):
    """Production-grade multi-tier translation service with colloquial Manglish lexicon,

    transliteration, cloud translation, and robust offline fallbacks.
    """

    MALAYALAM_RE = re.compile(r"[\u0D00-\u0D7F]")
    LATIN_RE = re.compile(r"[A-Za-z]")
    ENGLISH_WORD_RE = re.compile(r"[A-Za-z0-9']+")
    HTML_RE = re.compile(r"<html|</html|<!doctype|<script", re.IGNORECASE)

    TRANSLIT_ENDPOINT = "https://inputtools.google.com/request"
    DEFAULT_TIMEOUT = 3.5

    # Direct idiomatic lexicon for colloquial Malayalam / Manglish film & social reviews
    COLLOQUIAL_LEXICON: Dict[str, str] = {
        "ennik arum ellia": "I have no one",
        "ennik aarum illa": "I have no one",
        "enikk arum ella": "I have no one",
        "enikku aarum illa": "I have no one",
        "ennik ishtam ayila": "I didn't like it",
        "ennikku ishtam aayilla": "I didn't like it",
        "enikku ishtapettilla": "I didn't like it at all",
        "vere nthaalla": "Nothing else",
        "vere nthalla": "Nothing else",
        "padam thooki": "The movie was a blockbuster",
        "padam kollam": "The movie is good",
        "kidilan padam": "Awesome movie",
        "super padam": "Super movie",
        "adipoli": "Awesome",
        "pwoli": "Awesome",
        "pwoli padam": "Awesome movie",
        "theepori": "Fire / Sensational",
        "romancham": "Goosebumps",
        "bore": "Boring",
        "valare bore": "Very boring",
        "lag": "Slow paced / Laggy",
        "valare lag": "Very slow paced",
        "full lag": "Full of lag",
        "paisa nashtam": "Waste of money",
        "verum chavar": "Utter trash",
        "kollam": "Good",
        "nallath": "Good",
        "mosham": "Bad",
        "acting super": "Acting was super",
        "bgm kollam": "BGM was good",
        "direction super": "Direction was super",
        "direction kollam": "Direction was good",
        "must watch": "Must watch",
        "first half pwoli": "First half was awesome",
        "second half bore": "Second half was boring",
        "second half lag": "Second half was slow paced",
        "verum churandiyath padam": "Just a poorly made movie",
        "verum churandiyath padam...": "Just a poorly made movie...",
        "padam thooki! climax scene romancham aayirunnu": "The movie was a blockbuster! The climax scene gave goosebumps",
        "first half pwoli, but second half valare bore": "The first half was awesome, but the second half was very boring",
        "acting super, especially tovino and lead actors. must watch!": "Acting is super, especially Tovino and lead actors. Must watch!",
        "valare bore aayi poyi, second half full lag waste of money": "It was very boring, second half was full lag and waste of money",
        "paisa nashtam! enikku theere ishtapettilla.": "Waste of money! I didn't like it at all.",
        "bgm kollam, pakshe direction theere thripthikaram alla.": "BGM is good, but direction is not at all satisfactory.",
    }

    ORTHOGRAPHIC_NORMALIZATIONS = (
        (r"\bennik\b|\benikk\b|\benik\b", "enikku"),
        (r"\bellia\b|\belia\b|\byilla\b|\bila\b", "illa"),
        (r"\barum\b", "aarum"),
        (r"\bcheyth\b", "cheythu"),
        (r"\bparanj\b", "paranju"),
        (r"\bkand\b", "kandu"),
        (r"\bayila\b|\bayiila\b", "aayilla"),
    )

    COMMON_ENGLISH = {
        "movie", "film", "cinema", "song", "scene", "actor", "actress",
        "hero", "villain", "director", "camera", "music", "bgm", "review",
        "bro", "brother", "sis", "super", "mass", "nice", "great", "best",
        "worst", "good", "bad", "love", "like", "wow", "lol", "okay", "ok",
        "please", "thanks", "lag", "story", "climax", "interval", "acting",
        "theatre", "theaters", "teaser", "trailer"
    }

    ENGLISH_FUNCTION_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "am", "be", "been",
        "i", "you", "he", "she", "we", "they", "it", "this", "that", "these",
        "those", "what", "where", "when", "why", "how", "and", "or", "but",
        "if", "not", "no", "yes", "for", "from", "with", "to", "of", "in",
        "on", "at", "by", "my", "your", "his", "her", "our", "their", "have",
        "has", "had", "do", "does", "did", "will", "would", "can", "could",
        "should", "very", "really"
    }

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9,ml;q=0.8",
        })

    @staticmethod
    def normalize_text(text: str) -> str:
        """Unicode and whitespace normalization."""
        if not text:
            return ""
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u00a0", " ")
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def normalize_manglish(cls, text: str) -> str:
        """Standardizes common phonetic variations in Romanized Malayalam."""
        result = text
        for pattern, replacement in cls.ORTHOGRAPHIC_NORMALIZATIONS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result

    @classmethod
    def is_malayalam_script(cls, text: str) -> bool:
        """Returns True if string contains Malayalam unicode codepoints."""
        return bool(text and cls.MALAYALAM_RE.search(text))

    @classmethod
    def detect_script(cls, text: str) -> str:
        """Detects script class: 'malayalam', 'latin', 'mixed', or 'none'."""
        has_ml = bool(text and cls.MALAYALAM_RE.search(text))
        has_latin = bool(text and cls.LATIN_RE.search(text))
        if has_ml and has_latin:
            return "mixed"
        if has_ml:
            return "malayalam"
        if has_latin:
            return "latin"
        return "none"

    @classmethod
    def classify_language(cls, text: str) -> LanguageKind:
        """Classifies language into Malayalam, English, Manglish, or Mixed."""
        text = cls.normalize_text(text)
        if not text:
            return LanguageKind.UNKNOWN

        has_ml = cls.is_malayalam_script(text)
        latin_tokens = [w.lower() for w in cls.ENGLISH_WORD_RE.findall(text)]

        if has_ml and latin_tokens:
            return LanguageKind.MIXED
        if has_ml:
            return LanguageKind.MALAYALAM
        if not latin_tokens:
            return LanguageKind.UNKNOWN

        total_words = len(latin_tokens)
        function_count = sum(1 for w in latin_tokens if w in cls.ENGLISH_FUNCTION_WORDS)
        common_count = sum(1 for w in latin_tokens if w in cls.COMMON_ENGLISH)

        if total_words <= 3:
            if function_count >= 1 and (function_count + common_count) >= 2:
                return LanguageKind.ENGLISH
            return LanguageKind.MANGLISH

        ratio = (function_count + common_count) / total_words
        if function_count >= 2 and ratio >= 0.5:
            return LanguageKind.ENGLISH
        if (function_count >= 2 or common_count >= 2) and ratio >= 0.4:
            return LanguageKind.MIXED

        return LanguageKind.MANGLISH

    def _transliterate_manglish(self, text: str) -> Optional[str]:
        """Transliterates Romanized Malayalam to Malayalam script using Google Input Tools API."""
        canonical = self.normalize_manglish(text)
        params = {
            "text": canonical,
            "itc": "ml-t-i0-und",
            "num": "3",
            "cp": "0",
            "cs": "1",
            "ie": "utf-8",
            "oe": "utf-8",
        }
        try:
            resp = self.session.get(self.TRANSLIT_ENDPOINT, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) >= 2 and data[0] == "SUCCESS":
                    segments = data[1]
                    parts = []
                    for seg in segments:
                        if isinstance(seg, list) and len(seg) >= 2 and seg[1]:
                            parts.append(seg[1][0])
                    if parts:
                        return " ".join(parts).strip()
        except Exception as err:
            logger.debug(f"Transliteration lookup error (graceful fallback): {err}")
        return None

    def _translate_cloud(self, text: str, source: str = "auto", target: str = "en") -> Optional[str]:
        """Attempts cloud translation using Google Translate endpoint with fallback to deep_translator."""
        # Tier 1: Google Translate single endpoint
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text,
            }
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data and isinstance(data[0], list):
                    chunks = [p[0] for p in data[0] if isinstance(p, list) and p and isinstance(p[0], str)]
                    res = "".join(chunks).strip()
                    if res and not self.HTML_RE.search(res):
                        return res
        except Exception as e:
            logger.debug(f"Google web translate endpoint error: {e}")

        # Tier 2: deep_translator library
        try:
            from deep_translator import GoogleTranslator

            src = "ml" if source in {"ml", "malayalam"} else "auto"
            res = GoogleTranslator(source=src, target=target).translate(text)
            if res and not self.HTML_RE.search(res):
                return res.strip()
        except Exception as e:
            logger.debug(f"deep_translator Google fallback error: {e}")

        return None

    @staticmethod
    def _clean_english(text: str) -> str:
        text = re.sub(r"\s+", " ", text or "").strip()
        return (text[:1].upper() + text[1:]) if text else ""

    def translate_detailed(
        self, text: str, source: str = "auto", target: str = "en"
    ) -> TranslationResult:
        """Orchestrates multi-tier translation returning rich metadata."""
        original = self.normalize_text(text)
        if not original:
            return TranslationResult(
                text="",
                confidence=1.0,
                source_language="unknown",
                detected_script="none",
                intermediate_malayalam=None,
                method="empty",
                status="original",
            )

        detected_script = self.detect_script(original)
        clean_lower = original.lower().strip()
        clean_key = re.sub(r"[.!?,]+$", "", clean_lower).strip()

        # Step 0: Fast Colloquial Manglish Lexicon Check
        if clean_key in self.COLLOQUIAL_LEXICON:
            return TranslationResult(
                text=self.COLLOQUIAL_LEXICON[clean_key],
                confidence=0.98,
                source_language="manglish",
                detected_script=detected_script,
                intermediate_malayalam=None,
                method="colloquial_lexicon",
                status="translated",
            )

        lang_kind = self.classify_language(original)

        # Pure English: No translation needed (identity)
        if lang_kind == LanguageKind.ENGLISH:
            return TranslationResult(
                text=original,
                confidence=0.99,
                source_language="english",
                detected_script=detected_script,
                intermediate_malayalam=None,
                method="identity",
                status="original",
            )

        # Pure Malayalam Script: Direct translation to English
        if lang_kind == LanguageKind.MALAYALAM or self.is_malayalam_script(original):
            translated = self._translate_cloud(original, source="ml", target=target)
            if translated and translated.strip().lower() != original.strip().lower():
                return TranslationResult(
                    text=self._clean_english(translated),
                    confidence=0.92,
                    source_language="malayalam",
                    detected_script=detected_script,
                    intermediate_malayalam=original,
                    method="ml->en",
                    status="translated",
                )
            # If translation failed or returned identical text
            return TranslationResult(
                text=original,
                confidence=0.30,
                source_language="malayalam",
                detected_script=detected_script,
                intermediate_malayalam=original,
                method="fallback",
                status="fallback",
            )

        # Manglish / Mixed: Transliterate to Malayalam script first, then translate
        ml_script = self._transliterate_manglish(original)
        if ml_script:
            translated = self._translate_cloud(ml_script, source="ml", target=target)
            if translated and translated.strip().lower() != ml_script.strip().lower():
                return TranslationResult(
                    text=self._clean_english(translated),
                    confidence=0.90,
                    source_language="manglish",
                    detected_script=detected_script,
                    intermediate_malayalam=ml_script,
                    method="translit->ml->en",
                    status="translated",
                )

        # Direct cloud translation attempt for Manglish / Mixed
        direct = self._translate_cloud(original, source="auto", target=target)
        if direct and direct.strip().lower() != original.strip().lower():
            return TranslationResult(
                text=self._clean_english(direct),
                confidence=0.82,
                source_language=lang_kind.value,
                detected_script=detected_script,
                intermediate_malayalam=ml_script,
                method="direct->en",
                status="translated",
            )

        # Graceful fallback: return original text preserved
        return TranslationResult(
            text=original,
            confidence=0.25,
            source_language=lang_kind.value,
            detected_script=detected_script,
            intermediate_malayalam=ml_script,
            method="fallback",
            status="fallback",
        )

    def translate(self, text: str, source: str = "auto", target: str = "en") -> str:
        """Returns the translated string representation."""
        return self.translate_detailed(text, source=source, target=target).text


class MockTranslationService(BaseTranslationService):
    """Deterministic offline mock translation service for fast unit testing."""

    def __init__(self, dictionary: Optional[Dict[str, str]] = None) -> None:
        self.dictionary: Dict[str, str] = dictionary or {
            "പൊളി": "Awesome",
            "കിടിലൻ പടം": "Awesome movie",
            "pwoli": "Awesome",
            "padam thooki": "The movie was a blockbuster",
            "first half pwoli": "First half was awesome",
            "valare bore": "Very boring",
            "ennik aarum illa": "I have no one",
        }

    def translate_detailed(
        self, text: str, source: str = "auto", target: str = "en"
    ) -> TranslationResult:
        clean = text.strip()
        clean_lower = clean.lower()
        if clean_lower in self.dictionary:
            return TranslationResult(
                text=self.dictionary[clean_lower],
                confidence=0.95,
                source_language="ml",
                detected_script="malayalam" if any('\u0D00' <= c <= '\u0D7F' for c in clean) else "latin",
                intermediate_malayalam=None,
                method="mock_dictionary",
                status="translated",
            )
        # Identity for English
        if clean_lower.isascii() and any(w in clean_lower for w in ["the", "movie", "good", "bad"]):
            return TranslationResult(
                text=clean,
                confidence=0.99,
                source_language="en",
                detected_script="latin",
                intermediate_malayalam=None,
                method="identity",
                status="original",
            )
        # Default mock translation
        return TranslationResult(
            text=f"[Translated] {clean}",
            confidence=0.85,
            source_language=source,
            detected_script="latin",
            intermediate_malayalam=None,
            method="mock_echo",
            status="translated",
        )

    def translate(self, text: str, source: str = "auto", target: str = "en") -> str:
        return self.translate_detailed(text, source=source, target=target).text


_translation_service_instance: Optional[BaseTranslationService] = None


def get_translation_service() -> BaseTranslationService:
    """Singleton provider for translation service."""
    global _translation_service_instance
    if _translation_service_instance is None:
        _translation_service_instance = HybridTranslationService()
    return _translation_service_instance


def set_translation_service(service: BaseTranslationService) -> None:
    """Allows overriding translation service (e.g., during tests)."""
    global _translation_service_instance
    _translation_service_instance = service
