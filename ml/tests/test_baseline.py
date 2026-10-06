"""Unit Tests for Baseline TF-IDF + Logistic Regression Classifier."""

import tempfile
import pytest
import numpy as np
from ml.models.baseline_model import BaselineClassifier
from ml.data.dataset_loader import prepare_dataset, SENTIMENT_LABELS


def test_baseline_fit_predict_probabilities():
    train_df, _, test_df, _ = prepare_dataset()

    model = BaselineClassifier(ngram_range=(1, 2), max_features=1000, random_state=42)
    model.fit(train_df["clean_text"].tolist(), train_df["label_id"].tolist())

    preds = model.predict(test_df["clean_text"].tolist())
    probs = model.predict_proba(test_df["clean_text"].tolist())

    assert len(preds) == len(test_df)
    assert probs.shape == (len(test_df), 5)

    # Assert probabilities sum to 1.0 for every sample
    for row in probs:
        assert np.isclose(np.sum(row), 1.0, atol=1e-4)


def test_baseline_save_and_load():
    train_df, _, test_df, _ = prepare_dataset()

    model = BaselineClassifier(random_state=42)
    model.fit(train_df["clean_text"].tolist(), train_df["label_id"].tolist())

    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name

    model.save(tmp_path)
    loaded_model = BaselineClassifier.load(tmp_path)

    sample = ["Padam kidilan aayirunnu!"]
    orig_prob = model.predict_proba(sample)
    loaded_prob = loaded_model.predict_proba(sample)

    assert np.allclose(orig_prob, loaded_prob)
