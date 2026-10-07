"""Authoritative Label Definitions for Kollamo.ai Sentiment Analysis.

Five discrete classes strictly codified:
0 = Positive
1 = Negative
2 = Neutral
3 = Mixed
4 = Unsupported
"""

from ml.models.taxonomy import (
    CLASS_ID_POSITIVE,
    CLASS_ID_NEGATIVE,
    CLASS_ID_NEUTRAL,
    CLASS_ID_MIXED,
    CLASS_ID_UNSUPPORTED,
    SENTIMENT_CLASSES,
    SENTIMENT_LABELS,
    ID2LABEL,
    ID2CLASS,
    LABEL2ID,
)

NUM_CLASSES = 5


def get_class_name(class_id: int) -> str:
    """Returns canonical TitleCase class name for given class ID."""
    if class_id not in ID2CLASS:
        raise ValueError(f"Invalid class ID {class_id}. Must be in range 0..4.")
    return ID2CLASS[class_id]


def get_label(class_id: int) -> str:
    """Returns lowercase label name for given class ID."""
    if class_id not in ID2LABEL:
        raise ValueError(f"Invalid class ID {class_id}. Must be in range 0..4.")
    return ID2LABEL[class_id]


def get_class_id(label_or_class: str) -> int:
    """Returns integer class ID (0..4) for given label string.

    Raises:
        ValueError: If label_or_class is not in the authoritative 5 classes.
    """
    if label_or_class not in LABEL2ID:
        raise ValueError(
            f"Unknown sentiment label '{label_or_class}'. "
            f"Must be one of {SENTIMENT_CLASSES} or {SENTIMENT_LABELS}."
        )
    return LABEL2ID[label_or_class]


__all__ = [
    "NUM_CLASSES",
    "CLASS_ID_POSITIVE",
    "CLASS_ID_NEGATIVE",
    "CLASS_ID_NEUTRAL",
    "CLASS_ID_MIXED",
    "CLASS_ID_UNSUPPORTED",
    "SENTIMENT_CLASSES",
    "SENTIMENT_LABELS",
    "ID2LABEL",
    "ID2CLASS",
    "LABEL2ID",
    "get_class_name",
    "get_label",
    "get_class_id",
]
