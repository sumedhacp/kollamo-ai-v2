# Model Card — Kollamo-MuRIL 5-Class Sentiment Classifier

## 1. Model Details

- **Model Name**: `kollamo-muril-sentiment-5class` (Kollamo-MuRIL-v1)
- **Model Type**: Sequence Classification Head on Google MuRIL Transformer Backbone
- **Base Architecture**: `google/muril-base-cased` (12 layers, 12 attention heads, 768 hidden dimensions, 110M parameters, max position length 512)
- **Base Model Source**: [https://huggingface.co/google/muril-base-cased](https://huggingface.co/google/muril-base-cased)
- **Distinction**: `google/muril-base-cased` is the base pretrained language representation model; `kollamo-muril-sentiment-5class` is the task-specific fine-tuned 5-class sequence classifier.
- **Primary Languages**: Malayalam (`ml`), Romanized Malayalam / Manglish (`ml-en`), English (`en`), Code-Mixed Malayalam-English
- **License**: MIT License / Academic Research Use
- **Contact / Author**: Kollamo.ai Academic MCA Research Team

---

## 2. Intended Use

### Primary Intended Uses
- Sentiment polarity classification for social media comments (YouTube, blogs, forums).
- Categorization across the discrete 5-class taxonomy: `Positive`, `Negative`, `Neutral`, `Mixed`, `Unsupported`.
- Processing code-mixed comments common in South Indian online spaces.

### Out-of-Scope & Misuse
- The model outputs class probabilities representing probabilistic confidence over discrete categories; it must **never** be interpreted as a literal percentage of human emotion.
- Not intended for automated censorship, moderation without human review, or psychological profiling.
- The base checkpoint `google/muril-base-cased` must **never** be used directly for production inference without task-specific fine-tuning.

---

## 3. Training & Preprocessing Data

- **Corpus**: Multi-script social comments containing native Malayalam script, Manglish transliterations, English, and complex code-mixing.
- **Data Partitioning**: 80% Train, 10% Validation, 10% Test (Held-out).
- **Preprocessing Pipeline**:
  - Unicode NFKC canonical normalization
  - Stripping external URLs and user mentions
  - Sanitization of non-printable control characters while strictly retaining Malayalam Zero-Width Joiners (ZWJ) and Non-Joiners (ZWNJ)
  - Repeated character reduction (max 2 consecutive repetitions)
  - Whitespace canonicalization
  - Strict preservation of original comment text alongside preprocessed tokens
- **Data Leakage Safeguards**: Strict verification ensuring zero text overlap between train, validation, and test splits.

---

## 4. Evaluation & Performance

### 5-Class Target Taxonomy
1. `0 = Positive`: Praise, delight, appreciation, satisfaction.
2. `1 = Negative`: Criticism, dissatisfaction, disgust, frustration.
3. `2 = Neutral`: Objective statements, queries, release information.
4. `3 = Mixed`: Dual-polarity comments expressing both praise and criticism.
5. `4 = Unsupported`: Non-linguistic noise, spam, emojis without text, or unsupported scripts.

### Baseline Benchmark
- **TF-IDF + Logistic Regression**:
  - Accuracy: 33.3% (Actual measured on held-out test split)
  - Macro F1: 0.3371
  - Mixed F1: 0.2857
  - Unsupported F1: 0.6667
  - Diagnostic Error Analysis: Fails on unseen slang, spelling variations, and code-mixing.

### Target vs. Actual Accuracy
- **Target Goal**: High-performance multilingual accuracy as specified by platform goals.
- **Actual Status**: Target accuracy is a goal, **never** claimed as current performance until experimental measurement is completed.

---

## 5. Ethical Considerations & Limitations

- **Sarcasm & Subtlety**: Irony and subtle sarcasm remain challenging for surface representations.
- **Transliteration Variance**: While MuRIL handles transliterated Indian languages better than standard mBERT, non-standard spelling permutations can still reduce confidence.
- **Probability Interpretation**: Class probabilities reflect model distribution over classes and must not be communicated as emotional percentages.
