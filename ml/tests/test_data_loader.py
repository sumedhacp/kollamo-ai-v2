"""Unit Tests for Dataset Loader, Partitioning, and Leakage Prevention."""

import pytest
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS, LABEL2ID


def test_prepare_dataset_splits_and_leakage():
    train_df, val_df, test_df, meta = prepare_dataset(test_size=0.2, val_size=0.1, random_state=42)

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    # Strict zero data leakage verification
    train_texts = set(train_df["clean_text"])
    test_texts = set(test_df["clean_text"])
    val_texts = set(val_df["clean_text"])

    assert len(train_texts.intersection(test_texts)) == 0, "Data leakage between train and test!"
    assert len(train_texts.intersection(val_texts)) == 0, "Data leakage between train and val!"
    assert len(val_texts.intersection(test_texts)) == 0, "Data leakage between val and test!"


def test_class_weights_and_labels():
    train_df, val_df, test_df, meta = prepare_dataset()

    assert set(meta["sentiment_labels"]) == set(SENTIMENT_LABELS)
    assert len(meta["class_weights"]) == 5

    # Check all weights are positive numbers
    for idx, weight in meta["class_weights"].items():
        assert weight > 0.0
