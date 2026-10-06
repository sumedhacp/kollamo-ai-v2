"""Inference Predictor Engine for Kollamo.ai.

Transforms raw social media comments into structured sentiment predictions:
text
  -> preprocessing (NFKC normalization, URL/mention cleanup, repetition reduction)
  -> script & language identification (Malayalam, Latin/Manglish, Mixed, English)
  -> neural / baseline feature representation
  -> 5-class classification distribution
  -> top sentiment class & confidence

NOTE ON PROBABILITIES:
In compliance with AGENTS.md, class probabilities represent the model's
probabilistic confidence distribution over the 5 discrete target classes,
NOT literal percentages of human emotion contained in the comment.
"""

from typing import Dict, Any, List, Union, Optional
import numpy as np
import torch
from ml.data.dataset_loader import SENTIMENT_LABELS, ID2LABEL, LABEL2ID
from ml.preprocessing.cleaner import clean_text
from ml.preprocessing.detector import analyze_script_and_language


class SentimentPredictor:
    """Production and evaluation inference engine for Kollamo.ai sentiment analysis."""

    def __init__(self, model: Any = None, tokenizer: Any = None, device: str = "cpu"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def predict_single(self, text: str) -> Dict[str, Any]:
        """Runs full inference pipeline on a single comment."""
        if not text or not text.strip():
            return {
                "original_text": text,
                "detected_language": "unknown",
                "detected_script": "Unknown",
                "sentiment": "unsupported",
                "confidence": 1.0,
                "class_probabilities": {label: (1.0 if label == "unsupported" else 0.0) for label in SENTIMENT_LABELS},
                "translation_status": "not_needed",
                "error": "Empty text provided",
            }

        cleaned = clean_text(text)
        meta = analyze_script_and_language(text)

        # Check if text became empty after cleanup or is pure symbol noise
        if not cleaned:
            return {
                "original_text": text,
                "detected_language": meta["language"],
                "detected_script": meta["script"],
                "sentiment": "unsupported",
                "confidence": 0.99,
                "class_probabilities": {label: (0.99 if label == "unsupported" else 0.0025) for label in SENTIMENT_LABELS},
                "translation_status": "not_needed",
            }

        # Model forward pass
        if hasattr(self.model, "predict_proba"):
            # Scikit-learn Pipeline
            probs = self.model.predict_proba([cleaned])[0]
        elif hasattr(self.model, "predict_probabilities") and self.tokenizer is not None:
            # PyTorch MuRIL Classifier
            inputs = self.tokenizer(
                cleaned,
                max_length=128,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            ).to(self.device)
            tensor_probs = self.model.predict_probabilities(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
            )[0]
            probs = tensor_probs.cpu().numpy()
        else:
            raise RuntimeError("Valid model instance or tokenizer is not loaded in SentimentPredictor.")

        # Ensure probabilities sum strictly to 1.0
        probs = np.clip(probs, 1e-6, 1.0)
        probs = probs / np.sum(probs)

        top_idx = int(np.argmax(probs))
        top_sentiment = ID2LABEL.get(top_idx, "unsupported")
        confidence = float(probs[top_idx])

        class_probabilities = {
            label: round(float(probs[idx]), 4)
            for idx, label in enumerate(SENTIMENT_LABELS)
        }

        # Determine translation necessity
        needs_translation = meta["language"] in ("ml", "ml-en") and meta["script"] != "Unknown"
        translation_status = "untranslated" if needs_translation else "not_needed"

        return {
            "original_text": text,
            "detected_language": meta["language"],
            "detected_script": meta["script"],
            "sentiment": top_sentiment,
            "confidence": round(confidence, 4),
            "class_probabilities": class_probabilities,
            "translation_status": translation_status,
        }

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Batch inference for high-throughput comment lists."""
        return [self.predict_single(t) for t in texts]
