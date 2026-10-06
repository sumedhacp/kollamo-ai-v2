# ML & NLP Engineering Rules — Kollamo.ai

## Core Model Requirement: Google MuRIL
- The sentiment classifier must utilize Google MuRIL (`google/muril-base-cased`) as its neural backbone.
- Fine-tune a classification head on top of pooled embeddings for the 5 target classes:
  1. `positive`
  2. `negative`
  3. `neutral`
  4. `mixed`
  5. `unsupported`
- Fine-tuning must use PyTorch and Hugging Face Transformers. Do not train MuRIL from scratch.

## Strict Restrictions
- **No Static/Keyword Dictionaries**: Do not implement sentiment scoring using static word lists (e.g. Afinn, SentiWordNet, or custom Malayalam positive/negative lists).
- **No Rule-Based Sentiment Heuristics**: Do not use conditional `if/else` sentiment scoring.
- **No Fictitious Metrics**: Never report fabricated accuracy, precision, recall, or F1 scores. All metrics must stem directly from evaluation on a held-out test split.

## Preprocessing Safeguards
- Allowed operations:
  - Unicode NFKC normalization
  - Canonical whitespace collapse
  - URL removal (`https?://\S+`)
  - User mention sanitization (`@username`)
  - Repeated character reduction (e.g. "poliiiiiiii" -> "polii")
  - Safe transliteration cleanup
- Prohibited operations:
  - Stripping native Malayalam script or diacritics
  - Deleting negation tokens (e.g., "alla", "illa", "not")
  - Translating all text prior to sentiment classification without empirical proof of benefit

## Baseline & Evaluation Requirements
- Maintain a baseline model: TF-IDF feature extraction + scikit-learn Logistic Regression.
- Deep model performance must be benchmarked against this baseline.
- Metrics calculated on test sets:
  - Accuracy
  - Macro-averaged Precision, Recall, and F1-score
  - Weighted F1-score
  - Per-class F1-scores
  - Multi-class Confusion Matrix
- Track artifact provenance: dataset commit, model checkpoint hash, hyperparameter config, random seed.
