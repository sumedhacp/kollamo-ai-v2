"""Unit Tests for Centralized Five-Class Sentiment Taxonomy."""

import pytest
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


def test_deterministic_class_ids():
    assert CLASS_ID_POSITIVE == 0
    assert CLASS_ID_NEGATIVE == 1
    assert CLASS_ID_NEUTRAL == 2
    assert CLASS_ID_MIXED == 3
    assert CLASS_ID_UNSUPPORTED == 4


def test_ordered_class_lists():
    assert SENTIMENT_CLASSES == ["Positive", "Negative", "Neutral", "Mixed", "Unsupported"]
    assert SENTIMENT_LABELS == ["positive", "negative", "neutral", "mixed", "unsupported"]


def test_id_to_label_and_class_mappings():
    for idx, label in enumerate(SENTIMENT_LABELS):
        assert ID2LABEL[idx] == label
    for idx, cls_name in enumerate(SENTIMENT_CLASSES):
        assert ID2CLASS[idx] == cls_name


def test_label_to_id_case_insensitivity():
    assert LABEL2ID["positive"] == 0
    assert LABEL2ID["Positive"] == 0
    assert LABEL2ID["negative"] == 1
    assert LABEL2ID["Negative"] == 1
    assert LABEL2ID["neutral"] == 2
    assert LABEL2ID["Neutral"] == 2
    assert LABEL2ID["mixed"] == 3
    assert LABEL2ID["Mixed"] == 3
    assert LABEL2ID["unsupported"] == 4
    assert LABEL2ID["Unsupported"] == 4
