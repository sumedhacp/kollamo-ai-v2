# Annotation Policy & Five-Class Sentiment Specification — Kollamo.ai

This document codifies the authoritative five-class sentiment taxonomy, annotation guidelines, dataset schema, and language coverage requirements for Kollamo.ai.

---

## 1. Five-Class Sentiment Taxonomy & Deterministic Mapping

All dataset annotations, tokenizers, neural loss functions, evaluation reports, and inference responses strictly observe this centralized integer mapping:

| Class ID | Canonical Label | Display Class | Definition & Polarity Boundary |
| :---: | :---: | :---: | :--- |
| **0** | `positive` | **Positive** | Predominantly favorable sentiment, praise, delight, approval, admiration, comedy appreciation, or satisfaction. |
| **1** | `negative` | **Negative** | Predominantly unfavorable sentiment, criticism, dissatisfaction, disgust, frustration, boredom, or negative review. |
| **2** | `neutral` | **Neutral** | Primarily factual, descriptive, informational, release queries, theater status, or commentary without emotional polarity. |
| **3** | `mixed` | **Mixed** | Coexistence of materially conflicting positive and negative sentiment in the same comment that cannot be reduced to a single polarity. |
| **4** | `unsupported` | **Unsupported** | Content that cannot reasonably receive a valid sentiment classification under platform rules (noise, spam, non-linguistic data). |

---

## 2. Detailed Annotation Guidelines

### 2.1 Positive
- **Scope**: Expressions of enjoyment, stellar performance praise, cinematic appreciation, anticipation fulfilled.
- **Examples**:
  - Malayalam: `"ഈ സിനിമ വളരെ മികച്ചതാണ്, അഭിനയം ഗംഭീരം!"`
  - Manglish: `"Padam kidilam aayirunnu, fully worth watching!"`
  - Code-Mixed: `"BGM and visuals vere level aayirunnu!"`
  - English: `"Outstanding masterpiece by the director."`

### 2.2 Negative
- **Scope**: Disappointment, harsh critique, weak script complaints, wasted budget, boredom.
- **Examples**:
  - Malayalam: `"വളരെ മോശം സിനിമ, സമയം കളഞ്ഞു."`
  - Manglish: `"Valare mosham padam, second half valinja chali."`
  - Code-Mixed: `"Worst movie experience, script was totally boring."`
  - English: `"Total disaster and complete waste of time."`

### 2.3 Neutral
- **Scope**: Factual questions, release date inquiries, cast queries, cinema booking details.
- **Examples**:
  - Malayalam: `"ഈ ചിത്രം ഒടിടിയിൽ എന്ന് വരും?"`
  - Manglish: `"Padam ott release eppozhanu?"`
  - Code-Mixed: `"Booking started in PVR Kochi?"`
  - English: `"Release date is scheduled for next Friday."`

### 2.4 Mixed
- **Critical Policy Rule**: A comment is **NOT** labeled `Mixed` merely because it contains the contrastive discourse marker `"but"` or `"pakshe"`. The annotation requires *materially conflicting emotional polarity*.
- **Examples**:
  - Malayalam: `"അഭിനയം മികച്ചതായിരുന്നു, പക്ഷെ തിരക്കഥ തീർത്തും നിരാശപ്പെടുത്തി."` (Acting great [Positive] vs script disappointing [Negative] $\rightarrow$ **Mixed**)
  - Manglish: `"Fahadh acting super aayirunnu pakshe lag sahikan pattilla."`
  - Code-Mixed: `"First half was pure comedy and fun, but second half completely fell apart."`
- **Counter-Examples**:
  - `"Acting nalla aayirunnu, pakshe njan nale kaanum"` $\rightarrow$ Factual continuation, NOT Mixed.

### 2.5 Unsupported
- **Strict Scope Boundaries**:
  - Empty strings or whitespace-only inputs.
  - Non-linguistic symbol sequences (e.g. `!@#$%^&*`, `.....?????`).
  - Pure URL links without associated user commentary.
  - Bot spam or commercial promotional gibberish.
  - Languages outside the project's supported Indic/English domain (e.g., Cyrillic, Chinese).
- **Prohibited Use**: Annotators and pipelines must **NEVER** use `Unsupported` as a convenient escape for difficult, sarcastic, or ambiguous comments. Genuine human comments with difficult sentiment must be classified into `Positive`, `Negative`, `Neutral`, or `Mixed`.

---

## 3. Dataset Schema & Schema Requirements

Every training, validation, and test sample must conform to the minimum schema:

```json
{
  "id": "comment_unique_identifier_string",
  "text": "Raw user comment text exactly as written",
  "label": "positive | negative | neutral | mixed | unsupported",
  "language": "ml | ml-en | en | unknown",
  "script": "Malayalam | Latin | Mixed | Unknown"
}
```

---

## 4. Multi-Script Language Coverage Requirements

To represent the authentic domain of South Indian cinema discussions, the training corpus must incorporate:

1. **Native Malayalam Script (`ml`)**: Dravidian Unicode range `[\u0D00-\u0D7F]` including chillaksharangal and conjuncts.
2. **Manglish / Romanized Malayalam (`ml-en`)**: Phonetic transliterations using Latin alphabet (`polichu`, `adipoli`, `mosham`, `thara`).
3. **Malayalam-English Code-Mixed (`ml-en`)**: Intra-sentential and inter-sentential mixing of English vocabulary and Malayalam grammar.
4. **Standard English (`en`)**: English reviews and critical analysis.

The exact corpus language distribution must be measured and documented, not assumed.

---

## 5. Pipeline Consistency Guarantee

The five-class taxonomy and unsupported-input policy defined here are applied identically across:
- `Data Annotation`
- `Dataset Loader & Partitioning`
- `MuRIL Training & Evaluation`
- `Inference Predictor Engine`
- `FastAPI Backend Service`
