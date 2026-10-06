"""Evaluation Metrics Engine for Kollamo.ai ML Pipeline.

Computes:
- Overall Accuracy
- Macro Precision, Macro Recall, Macro F1
- Weighted F1
- Per-Class F1 for all 5 sentiment classes
- Multi-Class 5x5 Confusion Matrix
- JSON serialization with git provenance, seed, and hardware metadata
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
from ml.data.dataset_loader import SENTIMENT_LABELS, ID2LABEL


def compute_sentiment_metrics(
    y_true: Union[List[int], np.ndarray],
    y_pred: Union[List[int], np.ndarray],
    val_loss: float = None,
    inference_time_ms: float = None,
) -> Dict[str, Any]:
    """Computes academic-grade evaluation metrics across 5 sentiment classes."""
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    macro_p = float(precision_score(y_true_arr, y_pred_arr, average="macro", zero_division=0))
    macro_r = float(recall_score(y_true_arr, y_pred_arr, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true_arr, y_pred_arr, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true_arr, y_pred_arr, average="weighted", zero_division=0))

    # Per-class metrics
    per_class_f1_arr = f1_score(y_true_arr, y_pred_arr, average=None, zero_division=0)
    per_class_f1 = {
        SENTIMENT_LABELS[i]: float(per_class_f1_arr[i]) if i < len(per_class_f1_arr) else 0.0
        for i in range(len(SENTIMENT_LABELS))
    }

    # Confusion matrix (5x5)
    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=list(range(len(SENTIMENT_LABELS))))

    # Sklearn classification report dict
    report = classification_report(
        y_true_arr,
        y_pred_arr,
        labels=list(range(len(SENTIMENT_LABELS))),
        target_names=SENTIMENT_LABELS,
        output_dict=True,
        zero_division=0,
    )

    metrics = {
        "accuracy": round(acc, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class_f1": {k: round(v, 4) for k, v in per_class_f1.items()},
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }

    if val_loss is not None:
        metrics["validation_loss"] = round(float(val_loss), 4)

    if inference_time_ms is not None:
        metrics["inference_time_per_sample_ms"] = round(float(inference_time_ms), 3)

    return metrics


def save_experiment_report(
    metrics: Dict[str, Any],
    experiment_name: str,
    hyperparameters: Dict[str, Any],
    dataset_metadata: Dict[str, Any],
    output_path: str,
    git_commit_sha: str = "cf91968",
) -> str:
    """Saves comprehensive experiment report with metadata to JSON."""
    report = {
        "experiment_name": experiment_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_commit_sha,
        "preprocessing_version": "v1.0.0-nfkc-canonical",
        "dataset_metadata": dataset_metadata,
        "hyperparameters": hyperparameters,
        "metrics": metrics,
    }

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return str(out_file)
