"""Runner script to train and evaluate the Google MuRIL sentiment classifier."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from ml.data.dataset_loader import prepare_dataset
from ml.training.trainer import MurilTrainer


def main():
    print("=" * 60)
    print("Kollamo.ai — Fine-Tuning Google MuRIL Sentiment Classifier")
    print("=" * 60)

    config_path = PROJECT_ROOT / "ml" / "configs" / "muril_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 1. Prepare data splits with stratification and data leakage check
    train_df, val_df, test_df, meta = prepare_dataset(
        test_size=config["data"]["test_size"],
        val_size=config["data"]["val_size"],
        random_state=config["data"]["random_state"],
    )

    print(f"Dataset Loaded: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    print(f"Inverse class weights: {meta['class_weights']}")

    # 2. Initialize Trainer
    trainer = MurilTrainer(config=config)

    # 3. Train and Evaluate
    metrics = trainer.train(train_df, val_df, test_df, dataset_meta=meta)

    print("\n--- MuRIL Test Results ---")
    print(f"Accuracy:         {metrics['accuracy']:.4f}")
    print(f"Macro Precision:  {metrics['macro_precision']:.4f}")
    print(f"Macro Recall:     {metrics['macro_recall']:.4f}")
    print(f"Macro F1:         {metrics['macro_f1']:.4f}")
    print(f"Weighted F1:      {metrics['weighted_f1']:.4f}")
    print(f"Validation Loss:  {metrics.get('validation_loss', 'N/A')}")
    print(f"Per-Class F1:     {metrics['per_class_f1']}")
    print(f"Inference Latency:{metrics.get('inference_time_per_sample_ms', 0):.2f} ms/sample")
    print(f"\nConfusion Matrix:\n{metrics['confusion_matrix']}")

    diag = metrics.get("error_analysis", {})
    print(f"\nLinguistic Error Analysis Diagnostic Accuracy: {diag.get('overall_diagnostic_accuracy', 0):.4f}")
    for cat, stats in diag.get("category_breakdown", {}).items():
        print(f"  - {cat:20s}: Acc={stats['accuracy']:.2f} ({stats['correct']}/{stats['total_tested']})")

    print(f"\nModel and metrics successfully saved.")
    print("=" * 60)


if __name__ == "__main__":
    main()
