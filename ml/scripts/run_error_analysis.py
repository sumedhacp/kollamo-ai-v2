"""Linguistic Error Analysis Runner Script for Kollamo.ai."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.baseline_model import BaselineClassifier
from ml.evaluation.error_analyzer import run_error_analysis


def main():
    print("=" * 60)
    print("Kollamo.ai — Linguistic Error Analysis Suite")
    print("Evaluating model performance across 8 distinct linguistic phenomena")
    print("=" * 60)

    model_path = PROJECT_ROOT / "ml" / "models" / "saved_weights" / "baseline_tfidf.joblib"
    if not model_path.exists():
        print("Model file not found. Please train baseline model first via python ml/scripts/train_baseline.py")
        sys.exit(1)

    model = BaselineClassifier.load(str(model_path))

    report = run_error_analysis(lambda texts: model.predict(texts))

    print(f"\nOverall Diagnostic Accuracy: {report['overall_diagnostic_accuracy'] * 100:.1f}%\n")
    print(f"{'Linguistic Category':<25} | {'Tested':<6} | {'Correct':<7} | {'Accuracy':<8} | {'Error Rate':<10}")
    print("-" * 65)

    for cat, stats in report["category_breakdown"].items():
        print(f"{cat:<25} | {stats['total_tested']:<6} | {stats['correct']:<7} | {stats['accuracy']*100:>6.1f}% | {stats['error_rate']*100:>8.1f}%")

    print("\nDetailed Probe Failures / Misclassifications:")
    print("-" * 65)
    for probe in report["detailed_probe_results"]:
        if not probe["is_correct"]:
            print(f"[{probe['category']}] \"{probe['text']}\"")
            print(f"  -> True: {probe['true_label']} | Pred: {probe['predicted_label']}\n")


if __name__ == "__main__":
    main()
