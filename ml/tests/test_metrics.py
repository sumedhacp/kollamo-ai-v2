"""Unit Tests for Evaluation Metrics Engine."""

import pytest
import numpy as np
from ml.evaluation.metrics import compute_sentiment_metrics, save_experiment_report
from ml.models.taxonomy import SENTIMENT_LABELS


def test_compute_sentiment_metrics_per_class_and_special_classes():
    # 5 samples representing each class correctly predicted
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 3, 4]

    metrics = compute_sentiment_metrics(y_true, y_pred, val_loss=0.45, inference_time_ms=12.5)

    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["weighted_f1"] == 1.0

    # Ensure all 5 classes have individual precision, recall, f1
    for label in SENTIMENT_LABELS:
        assert label in metrics["per_class_precision"]
        assert label in metrics["per_class_recall"]
        assert label in metrics["per_class_f1"]

    # First-class Mixed evaluation
    assert "mixed_class_evaluation" in metrics
    mixed_eval = metrics["mixed_class_evaluation"]
    assert mixed_eval["precision"] == 1.0
    assert mixed_eval["recall"] == 1.0
    assert mixed_eval["f1"] == 1.0
    assert mixed_eval["support"] == 1

    # First-class Unsupported evaluation
    assert "unsupported_class_evaluation" in metrics
    unsupported_eval = metrics["unsupported_class_evaluation"]
    assert unsupported_eval["precision"] == 1.0
    assert unsupported_eval["recall"] == 1.0
    assert unsupported_eval["f1"] == 1.0
    assert unsupported_eval["support"] == 1

    # 5x5 confusion matrix
    cm = metrics["confusion_matrix"]
    assert len(cm) == 5
    for row in cm:
        assert len(row) == 5


def test_metrics_mixed_confusion_capture():
    # Mixed (class 3) misclassified as Positive (class 0)
    y_true = [3, 3, 1, 2, 4]
    y_pred = [0, 3, 1, 2, 4]

    metrics = compute_sentiment_metrics(y_true, y_pred)
    assert metrics["mixed_class_evaluation"]["recall"] == 0.5
    assert metrics["mixed_class_evaluation"]["support"] == 2
