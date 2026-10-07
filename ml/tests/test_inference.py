"""Unit Tests for Sentiment Predictor Engine."""

import pytest
import numpy as np
from ml.models.baseline_model import BaselineClassifier
from ml.inference.predictor import SentimentPredictor
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS
from ml.exceptions import InferenceError


@pytest.fixture(scope="module")
def trained_baseline_predictor():
    train_df, _, _, _ = prepare_dataset()
    model = BaselineClassifier(random_state=42)
    model.fit(train_df["clean_text"].tolist(), train_df["label_id"].tolist())
    return SentimentPredictor(model=model, device="cpu")


def test_predictor_schema_and_probability_distribution(trained_baseline_predictor):
    result = trained_baseline_predictor.predict_single("Padam kidilam aayirunnu, fully worth!")

    assert "original_text" in result
    assert "detected_language" in result
    assert "detected_script" in result
    assert "sentiment" in result
    assert "confidence" in result
    assert "class_probabilities" in result
    assert "translation_status" in result
    assert "model_metadata" in result
    assert "processing_metadata" in result

    assert result["sentiment"] in SENTIMENT_LABELS
    assert 0.0 <= result["confidence"] <= 1.0

    # Ensure all 5 classes are present
    assert set(result["class_probabilities"].keys()) == set(SENTIMENT_LABELS)

    # Ensure class probabilities sum to 1.0
    total_prob = sum(result["class_probabilities"].values())
    assert np.isclose(total_prob, 1.0, atol=1e-3)

    # Ensure confidence matches top class probability
    top_label = result["sentiment"]
    assert np.isclose(result["confidence"], result["class_probabilities"][top_label], atol=1e-3)

    # Check metadata fields
    assert "architecture" in result["model_metadata"]
    assert "inference_time_ms" in result["processing_metadata"]


def test_predictor_empty_text_handling():
    predictor = SentimentPredictor(model=None)
    result = predictor.predict_single("   ")

    assert result["sentiment"] == "unsupported"
    assert result["confidence"] == 1.0
    assert result["class_probabilities"]["unsupported"] == 1.0
    assert result["processing_metadata"]["cleaned_length"] == 0


def test_predictor_none_and_non_string_handling():
    predictor = SentimentPredictor(model=None)
    result_none = predictor.predict_single(None)
    assert result_none["sentiment"] == "unsupported"
    assert result_none["confidence"] == 1.0

    result_num = predictor.predict_single(12345)
    assert result_num["sentiment"] == "unsupported"


def test_predictor_noise_reduction_handling():
    predictor = SentimentPredictor(model=None)
    # A string containing only URLs and user mentions
    result = predictor.predict_single("@user https://example.com/test @another")
    assert result["sentiment"] == "unsupported"
    assert result["confidence"] >= 0.95
    assert result["class_probabilities"]["unsupported"] >= 0.95


def test_predictor_batch_inference(trained_baseline_predictor):
    comments = [
        "Super movie, enjoyed every bit!",
        "Very bad film, waste of money",
        "  ",
    ]
    results = trained_baseline_predictor.predict_batch(comments)
    assert len(results) == 3
    assert results[0]["sentiment"] in SENTIMENT_LABELS
    assert results[1]["sentiment"] in SENTIMENT_LABELS
    assert results[2]["sentiment"] == "unsupported"


def test_predictor_unconfigured_model_raises_inference_error():
    predictor = SentimentPredictor(model="invalid_model_without_predict")
    with pytest.raises(InferenceError):
        predictor.predict_single("Some valid comment text")
