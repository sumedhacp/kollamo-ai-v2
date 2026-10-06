# Model Card — Kollamo-MuRIL Sentiment Classifier

## 1. Model Details

- **Model Name**: Kollamo-MuRIL-v1
- **Model Type**: Transformer-based Sequence Classification Head on Google MuRIL Backbone
- **Base Architecture**: `google/muril-base-cased` (12 layers, 768 hidden dimensions, 12 attention heads, 110M parameters)
- **Primary Languages**: Malayalam (`ml`), Romanized Malayalam / Manglish (`ml-en`), English (`en`), Code-Mixed Malayalam-English
- **License**: MIT License / Academic Research Use
- **Contact / Author**: Kollamo.ai Academic MCA Research Team

---

## 2. Intended Use

### Primary Intended Uses
- Sentiment polarity classification for social media comments (YouTube, blogs, forums).
- Distinguishing positive, negative, neutral, mixed, and unsupported noise.
- Processing code-mixed comments common in South Indian online spaces.

### Out-of-Scope & Misuse
- The model outputs class probabilities representing probabilistic confidence over discrete categories; it must **never** be interpreted as a literal percentage of human emotion.
- Not intended for automated censorship, moderation without human review, or psychological profiling.

---

## 3. Training & Preprocessing Data

- **Corpus**: Multi-script social comments containing native Malayalam script, Manglish transliterations, English, and complex code-mixing.
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
1. `positive`: Praise, delight, appreciation, satisfaction.
2. `negative`: Criticism, dissatisfaction, disgust, frustration.
3. `neutral`: Objective statements, queries, release information.
4. `mixed`: Dual-polarity comments expressing both praise and criticism.
5. `unsupported`: Non-linguistic noise, spam, emojis without text, or unsupported scripts.

### Baseline Benchmark
- **TF-IDF + Logistic Regression**:
  - Accuracy: 33.3%
  - Macro F1: 0.3371
  - Diagnostic Error Analysis: Fails on unseen slang, spelling variations, and code-mixing.

---

## 5. Ethical Considerations & Limitations

- **Sarcasm & Subtlety**: Irony and subtle sarcasm remain challenging for surface representations.
- **Transliteration Variance**: While MuRIL handles transliterated Indian languages better than standard mBERT, non-standard spelling permutations can still reduce confidence.
- **Probability Interpretation**: Class probabilities reflect model distribution over classes and must not be communicated as emotional percentages.
