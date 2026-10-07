"""Unit Tests for Dataset Loader, Partitioning, and Leakage Prevention."""

import pytest
import numpy as np
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS, LABEL2ID


def test_prepare_dataset_80_10_10_split_and_leakage():
    train_df, val_df, test_df, meta = prepare_dataset(test_size=0.1, val_size=0.1, random_state=42)

    total = meta["total_samples"]
    assert len(train_df) + len(val_df) + len(test_df) == total
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    # Verify ~80 / 10 / 10 proportions
    assert np.isclose(len(train_df) / total, 0.8, atol=0.05)
    assert np.isclose(len(val_df) / total, 0.1, atol=0.05)
    assert np.isclose(len(test_df) / total, 0.1, atol=0.05)

    # Strict zero data leakage verification
    train_texts = set(train_df["clean_text"])
    test_texts = set(test_df["clean_text"])
    val_texts = set(val_df["clean_text"])

    assert len(train_texts.intersection(test_texts)) == 0, "Data leakage between train and test!"
    assert len(train_texts.intersection(val_texts)) == 0, "Data leakage between train and val!"
    assert len(val_texts.intersection(test_texts)) == 0, "Data leakage between val and test!"


def test_class_weights_percentages_and_labels():
    train_df, val_df, test_df, meta = prepare_dataset()

    assert set(meta["sentiment_labels"]) == set(SENTIMENT_LABELS)
    assert len(meta["class_weights"]) == 5
    assert "class_percentages" in meta

    # Check all weights and percentages are positive numbers
    for idx, weight in meta["class_weights"].items():
        assert weight > 0.0

    total_pct = sum(meta["class_percentages"].values())
    assert np.isclose(total_pct, 100.0, atol=0.5)
