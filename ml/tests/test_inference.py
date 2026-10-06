"""Unit Tests for Sentiment Predictor Engine."""

import pytest
import numpy as np
from ml.models.baseline_model import BaselineClassifier
from ml.inference.predictor import SentimentPredictor
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS


def test_predictor_schema_and_probability_distribution():
    train_df, _, _, _ = prepare_dataset()
    model = BaselineClassifier(random_state=42)
    model.fit(train_df["clean_text"].tolist(), train_df["label_id"].tolist())

    predictor = SentimentPredictor(model=model)

    result = predictor.predict_single("Padam kidilam aayirunnu, fully worth!")

    assert "original_text" in result
    assert "detected_language" in result
    assert "detected_script" in result
    assert "sentiment" in result
    assert "confidence" in result
    assert "class_probabilities" in result
    assert "translation_status" in result

    assert result["sentiment"] in SENTIMENT_LABELS
    assert 0.0 <= result["confidence"] <= 1.0

    # Ensure all 5 classes are present
    assert set(result["class_probabilities"].keys()) == set(SENTIMENT_LABELS)

    # Ensure class probabilities sum to 1.0
    total_prob = sum(result["class_probabilities"].values())
    assert np.isclose(total_prob, 1.0, atol=1e-3)


def test_predictor_empty_text_handling():
    predictor = SentimentPredictor(model=None)
    result = predictor.predict_single("   ")

    assert result["sentiment"] == "unsupported"
    assert result["confidence"] == 1.0
