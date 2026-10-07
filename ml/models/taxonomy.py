"""Centralized, Deterministic Five-Class Sentiment Taxonomy for Kollamo.ai.

Strictly codifies the five discrete target classes:
0 = Positive
1 = Negative
2 = Neutral
3 = Mixed
4 = Unsupported

Ensures deterministic mapping across all data loading, preprocessing,
training, evaluation, and inference layers.
"""

from typing import Dict, List

# Authoritative Integer Class IDs
CLASS_ID_POSITIVE = 0
CLASS_ID_NEGATIVE = 1
CLASS_ID_NEUTRAL = 2
CLASS_ID_MIXED = 3
CLASS_ID_UNSUPPORTED = 4

# Deterministic Ordered Class Lists
SENTIMENT_CLASSES: List[str] = [
    "Positive",
    "Negative",
    "Neutral",
    "Mixed",
    "Unsupported",
]

SENTIMENT_LABELS: List[str] = [
    "positive",
    "negative",
    "neutral",
    "mixed",
    "unsupported",
]

# ID to Label Mappings
ID2LABEL: Dict[int, str] = {
    CLASS_ID_POSITIVE: "positive",
    CLASS_ID_NEGATIVE: "negative",
    CLASS_ID_NEUTRAL: "neutral",
    CLASS_ID_MIXED: "mixed",
    CLASS_ID_UNSUPPORTED: "unsupported",
}

ID2CLASS: Dict[int, str] = {
    CLASS_ID_POSITIVE: "Positive",
    CLASS_ID_NEGATIVE: "Negative",
    CLASS_ID_NEUTRAL: "Neutral",
    CLASS_ID_MIXED: "Mixed",
    CLASS_ID_UNSUPPORTED: "Unsupported",
}

# Label to ID Mappings (case-insensitive support for robust ingestion)
LABEL2ID: Dict[str, int] = {
    "positive": CLASS_ID_POSITIVE,
    "negative": CLASS_ID_NEGATIVE,
    "neutral": CLASS_ID_NEUTRAL,
    "mixed": CLASS_ID_MIXED,
    "unsupported": CLASS_ID_UNSUPPORTED,
    "Positive": CLASS_ID_POSITIVE,
    "Negative": CLASS_ID_NEGATIVE,
    "Neutral": CLASS_ID_NEUTRAL,
    "Mixed": CLASS_ID_MIXED,
    "Unsupported": CLASS_ID_UNSUPPORTED,
}
