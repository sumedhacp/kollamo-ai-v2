"""ML Schema Contracts for Sentiment Inference and Training.

Defines decoupled input/output contracts for the ML layer without loading models.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from ml.models.taxonomy import SENTIMENT_LABELS, SENTIMENT_CLASSES, LABEL2ID


def validate_label(label: str) -> str:
    """Validates that a label belongs strictly to the authoritative 5 sentiment classes.

    Raises:
        ValueError: If the label is not in ['Positive', 'Negative', 'Neutral', 'Mixed', 'Unsupported']
                    or their canonical lowercase forms.
    """
    if label not in LABEL2ID:
        raise ValueError(
            f"Invalid sentiment label '{label}'. Label must be one of: {SENTIMENT_CLASSES} "
            f"or canonical lowercase {SENTIMENT_LABELS}."
        )
    return label.lower()


@dataclass
class SentimentPredictionContract:
    """Logical contract for single-comment sentiment prediction result."""

    original_text: str
    sentiment: str
    confidence: float
    class_probabilities: Dict[str, float]
    detected_language: str
    detected_script: str
    translation_status: str
    model_metadata: Dict[str, Any] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate sentiment class
        if self.sentiment not in SENTIMENT_LABELS and self.sentiment not in SENTIMENT_CLASSES:
            raise ValueError(f"Prediction sentiment '{self.sentiment}' must be in {SENTIMENT_LABELS}")

        # Validate confidence bounds
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence score {self.confidence} must be between 0.0 and 1.0")

        # Validate class probabilities keys and bounds
        for label in SENTIMENT_LABELS:
            if label not in self.class_probabilities:
                raise ValueError(f"Missing probability for class '{label}'")
            prob = self.class_probabilities[label]
            if not (0.0 <= prob <= 1.0):
                raise ValueError(f"Probability for '{label}' ({prob}) must be between 0.0 and 1.0")


@dataclass
class TrainingSampleContract:
    """Logical contract for a labeled training, validation, or test sample."""

    id: str
    text: str
    label: str
    language: Optional[str] = "unknown"
    script: Optional[str] = "Unknown"

    def __post_init__(self):
        if not self.text or not isinstance(self.text, str) or not self.text.strip():
            # If text is empty, label must be Unsupported per annotation policy
            if self.label.lower() != "unsupported":
                raise ValueError("Empty or whitespace text must have label 'Unsupported'")

        validate_label(self.label)
