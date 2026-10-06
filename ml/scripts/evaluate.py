"""Standalone evaluation script for model evaluation on test data."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS
from ml.models.baseline_model import BaselineClassifier
from ml.evaluation.metrics import compute_sentiment_metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate Kollamo.ai sentiment model")
    parser.add_argument("--model_path", type=str, default="ml/models/saved_weights/baseline_tfidf.joblib", help="Path to serialized model")
    parser.add_argument("--model_type", type=str, default="baseline", choices=["baseline", "muril"], help="Model architecture")
    args = parser.parse_args()

    print(f"Loading test split and evaluating {args.model_type} from {args.model_path}...")

    _, _, test_df, meta = prepare_dataset()

    if args.model_type == "baseline":
        model = BaselineClassifier.load(str(PROJECT_ROOT / args.model_path))
        y_pred = model.predict(test_df["clean_text"].tolist())
    else:
        raise NotImplementedError("MuRIL standalone evaluation requires PyTorch checkpoint loading.")

    y_true = test_df["label_id"].tolist()
    metrics = compute_sentiment_metrics(y_true, y_pred)

    print("\n" + "=" * 50)
    print("EVALUATION REPORT")
    print("=" * 50)
    print(f"Accuracy:        {metrics['accuracy']:.4f}")
    print(f"Macro Precision: {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:    {metrics['macro_recall']:.4f}")
    print(f"Macro F1:        {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:     {metrics['weighted_f1']:.4f}")
    print("\nPer-Class F1:")
    for label in SENTIMENT_LABELS:
        print(f"  {label:12s}: {metrics['per_class_f1'].get(label, 0.0):.4f}")
    print("\nConfusion Matrix:")
    print(metrics["confusion_matrix"])
    print("=" * 50)


if __name__ == "__main__":
    main()
