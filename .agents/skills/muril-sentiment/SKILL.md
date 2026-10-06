---
name: muril-sentiment
description: >-
  Use this skill when developing, training, evaluating, or running inference with the
  Google MuRIL multilingual sentiment classification model for Malayalam and Manglish.
---

# MuRIL Multilingual Sentiment Skill

This skill guides the fine-tuning, evaluation, and inference workflows for Google MuRIL on Malayalam, Manglish, English, and code-mixed comments.

## Supported Sentiment Classes
1. `positive`
2. `negative`
3. `neutral`
4. `mixed`
5. `unsupported`

## Workflow Procedures

### 1. Preprocessing Workflow
- Input text must pass through `ml.preprocessing.cleaner.clean_comment()`:
  - Unicode NFKC normalization
  - Canonical whitespace collapse
  - Regex stripping of URLs and mentions
  - Repetition normalization (max 2 consecutive repeated characters)
- Raw text must always be retained for display and translation.

### 2. Baseline Model
- TF-IDF with sublinear TF scaling + n-grams `(1, 2)`.
- Logistic Regression with cross-validation.
- Evaluate on test set before training MuRIL to establish the benchmark.

### 3. MuRIL Fine-Tuning
- Backbone: `google/muril-base-cased`
- Sequence Length: 128 tokens
- Optimizer: AdamW with weight decay `0.01`
- Learning Rate: `2e-5` with linear warmup and cosine decay
- Evaluation Strategy: Evaluate every epoch; checkpoint best model by Macro F1.
- Weighted Cross-Entropy: Apply class weights computed as `total_samples / (n_classes * class_count)` when class imbalance is detected.

### 4. Metrics Reporting
- Compute confusion matrix and classification report using `sklearn.metrics`.
- Record:
  - Accuracy
  - Macro Precision, Recall, F1
  - Weighted F1
  - Per-class F1
- Save metrics artifact to `ml/evaluation/reports/` with run timestamp, config, and git commit hash.
