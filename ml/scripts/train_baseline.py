"""Script to train and evaluate the TF-IDF + Logistic Regression baseline model."""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS
from ml.models.baseline_model import BaselineClassifier
from ml.evaluation.metrics import compute_sentiment_metrics, save_experiment_report
from ml.evaluation.error_analyzer import run_error_analysis


def main():
    print("=" * 60)
    print("Kollamo.ai — Training Baseline Classifier (TF-IDF + LogReg)")
    print("=" * 60)

    config_path = PROJECT_ROOT / "ml" / "configs" / "baseline_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 1. Prepare data splits
    train_df, val_df, test_df, meta = prepare_dataset(
        test_size=config["data"]["test_size"],
        val_size=config["data"]["val_size"],
        random_state=config["data"]["random_state"],
    )

    print(f"Dataset summary: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    print(f"Class distribution: {meta['class_counts']}")

    # 2. Fit baseline model
    model = BaselineClassifier(
        ngram_range=tuple(config["vectorizer"]["ngram_range"]),
        max_features=config["vectorizer"]["max_features"],
        sublinear_tf=config["vectorizer"]["sublinear_tf"],
        C=config["classifier"]["C"],
        random_state=config["classifier"]["random_state"],
    )

    print("\nTraining baseline model...")
    start_train = time.time()
    model.fit(train_df["clean_text"].tolist(), train_df["label_id"].tolist())
    train_duration = time.time() - start_train
    print(f"Training completed in {train_duration:.3f}s")

    # 3. Test evaluation
    start_infer = time.time()
    y_pred = model.predict(test_df["clean_text"].tolist())
    infer_time_ms = ((time.time() - start_infer) / len(test_df)) * 1000.0

    y_true = test_df["label_id"].tolist()
    metrics = compute_sentiment_metrics(y_true, y_pred, inference_time_ms=infer_time_ms)

    print("\n--- Baseline Test Results ---")
    print(f"Accuracy:         {metrics['accuracy']:.4f}")
    print(f"Macro Precision:  {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:     {metrics['macro_recall']:.4f}")
    print(f"Macro F1:         {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:      {metrics['weighted_f1']:.4f}")
    print(f"Per-Class F1:     {metrics['per_class_f1']}")
    print(f"Confusion Matrix:\n{metrics['confusion_matrix']}")

    # 4. Error Analysis across linguistic phenomena
    print("\nRunning Error Analysis on 8 linguistic phenomena...")
    error_report = run_error_analysis(lambda texts: model.predict([texts[0] if isinstance(texts, list) else texts]))
    print(f"Diagnostic Accuracy: {error_report['overall_diagnostic_accuracy']:.4f}")
    for cat, stats in error_report["category_breakdown"].items():
        print(f"  - {cat:20s}: Acc={stats['accuracy']:.2f} ({stats['correct']}/{stats['total_tested']})")

    # 5. Save artifacts
    weights_path = PROJECT_ROOT / "ml" / "models" / "saved_weights" / "baseline_tfidf.joblib"
    model.save(str(weights_path))
    print(f"\nModel saved to: {weights_path}")

    metrics["error_analysis"] = error_report
    report_path = PROJECT_ROOT / "ml" / "evaluation" / "reports" / "baseline_metrics.json"
    save_experiment_report(
        metrics=metrics,
        experiment_name=config["experiment_name"],
        hyperparameters=config,
        dataset_metadata=meta,
        output_path=str(report_path),
        git_commit_sha="cf91968",
    )
    print(f"Evaluation report saved to: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
