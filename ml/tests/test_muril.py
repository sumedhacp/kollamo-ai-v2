"""Unit Tests for MuRIL Classifier Architecture and Forward Pass."""

import pytest
import torch
from ml.models.muril_classifier import MurilSentimentClassifier, MurilClassificationHead


def test_muril_classification_head():
    head = MurilClassificationHead(hidden_size=768, num_classes=5, dropout_prob=0.1)
    dummy_features = torch.randn(4, 768)
    logits = head(dummy_features)

    assert logits.shape == (4, 5)


def test_muril_forward_pass_shapes():
    # Test classifier initialization and forward pass with mock inputs
    classifier = MurilSentimentClassifier(
        model_name="google/muril-base-cased",
        num_classes=5,
        pretrained=False,  # Use random config initialization to test shapes quickly
    )

    batch_size = 2
    seq_len = 16
    input_ids = torch.randint(0, 1000, (batch_size, seq_len))
    attention_mask = torch.ones((batch_size, seq_len))

    logits = classifier(input_ids, attention_mask)
    assert logits.shape == (batch_size, 5)

    probs = classifier.predict_probabilities(input_ids, attention_mask)
    assert probs.shape == (batch_size, 5)

    # Check softmax sum to 1
    row_sums = torch.sum(probs, dim=-1)
    for s in row_sums:
        assert torch.isclose(s, torch.tensor(1.0), atol=1e-4)
