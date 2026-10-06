"""Baseline Sentiment Classifier using TF-IDF + Logistic Regression."""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from ml.data.dataset_loader import SENTIMENT_LABELS, LABEL2ID, ID2LABEL


class BaselineClassifier:
    """TF-IDF and Logistic Regression pipeline establishing the classical baseline."""

    def __init__(
        self,
        ngram_range: Tuple[int, int] = (1, 2),
        max_features: int = 5000,
        sublinear_tf: bool = True,
        C: float = 1.0,
        random_state: int = 42,
    ):
        self.pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=ngram_range,
                    max_features=max_features,
                    sublinear_tf=sublinear_tf,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=C,
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=random_state,
                ),
            ),
        ])
        self.is_fitted = False

    def fit(self, texts: List[str], labels: List[int]) -> "BaselineClassifier":
        """Fit TF-IDF and Logistic Regression on training split."""
        self.pipeline.fit(texts, labels)
        self.is_fitted = True
        return self

    def predict(self, texts: List[str]) -> np.ndarray:
        """Predict class IDs (0..4)."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() first.")
        return self.pipeline.predict(texts)

    def predict_proba(self, texts: List[str]) -> np.ndarray:
        """Predict class probability distributions."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() first.")
        return self.pipeline.predict_proba(texts)

    def predict_single(self, text: str) -> Dict[str, Any]:
        """Classifies a single text and formats confidence and probabilities."""
        proba = self.predict_proba([text])[0]
        top_idx = int(np.argmax(proba))
        top_label = ID2LABEL[top_idx]
        top_confidence = float(proba[top_idx])

        class_probabilities = {
            label: float(proba[idx]) for idx, label in enumerate(SENTIMENT_LABELS)
        }

        return {
            "sentiment": top_label,
            "confidence": round(top_confidence, 4),
            "class_probabilities": class_probabilities,
        }

    def save(self, filepath: str) -> None:
        """Serializes fitted pipeline to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, filepath)

    @classmethod
    def load(cls, filepath: str) -> "BaselineClassifier":
        """Loads fitted pipeline from disk."""
        instance = cls()
        instance.pipeline = joblib.load(filepath)
        instance.is_fitted = True
        return instance
