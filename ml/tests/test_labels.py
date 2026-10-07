"""Unit Tests for Authoritative Label Definitions."""

import pytest
from ml.models.labels import (
    NUM_CLASSES,
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
    get_class_name,
    get_label,
    get_class_id,
)


def test_exactly_five_labels():
    assert NUM_CLASSES == 5
    assert len(SENTIMENT_CLASSES) == 5
    assert len(SENTIMENT_LABELS) == 5
    assert len(ID2LABEL) == 5
    assert len(ID2CLASS) == 5


def test_deterministic_label_mapping():
    assert CLASS_ID_POSITIVE == 0
    assert CLASS_ID_NEGATIVE == 1
    assert CLASS_ID_NEUTRAL == 2
    assert CLASS_ID_MIXED == 3
    assert CLASS_ID_UNSUPPORTED == 4

    assert get_class_name(0) == "Positive"
    assert get_class_name(1) == "Negative"
    assert get_class_name(2) == "Neutral"
    assert get_class_name(3) == "Mixed"
    assert get_class_name(4) == "Unsupported"

    assert get_label(0) == "positive"
    assert get_label(1) == "negative"
    assert get_label(2) == "neutral"
    assert get_label(3) == "mixed"
    assert get_label(4) == "unsupported"


def test_reject_unknown_labels():
    with pytest.raises(ValueError):
        get_class_id("VeryPositive")

    with pytest.raises(ValueError):
        get_class_id("NegativeSad")

    with pytest.raises(ValueError):
        get_class_id("invalid_label")

    with pytest.raises(ValueError):
        get_class_name(5)

    with pytest.raises(ValueError):
        get_label(-1)
