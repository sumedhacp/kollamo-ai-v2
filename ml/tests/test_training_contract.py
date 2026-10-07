"""Unit Tests for Training Data Contract and Pipeline Foundations."""

import pytest
import yaml
from pathlib import Path
from ml.schemas.sentiment import TrainingSampleContract, validate_label
from ml.models.labels import SENTIMENT_CLASSES, SENTIMENT_LABELS
from ml.data.dataset_loader import prepare_dataset
from ml.evaluation.metrics import compute_sentiment_metrics


def test_training_sample_contract_valid():
    sample = TrainingSampleContract(
        id="c123",
        text="ഈ സിനിമ വളരെ മികച്ചതാണ്!",
        label="Positive",
        language="ml",
        script="Malayalam",
    )
    assert sample.id == "c123"
    assert sample.label == "Positive"


def test_training_sample_contract_rejects_unknown_label():
    with pytest.raises(ValueError):
        TrainingSampleContract(
            id="c124",
            text="Decent film",
            label="SomewhatPositive",
        )


def test_training_sample_empty_text_must_be_unsupported():
    # Empty text labeled Positive must fail validation
    with pytest.raises(ValueError):
        TrainingSampleContract(
            id="c125",
            text="   ",
            label="Positive",
        )

    # Empty text labeled Unsupported succeeds
    sample = TrainingSampleContract(
        id="c126",
        text="   ",
        label="Unsupported",
    )
    assert sample.label == "Unsupported"


def test_training_configuration_schema():
    config_path = Path(__file__).parent.parent / "configs" / "muril_config.yaml"
    assert config_path.exists(), "muril_config.yaml must exist in ml/configs"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Assert required configuration keys
    assert config["model"]["base_model"] == "google/muril-base-cased"
    assert config["model"]["num_labels"] == 5
    assert config["hyperparameters"]["max_length"] <= 512
    assert config["hyperparameters"]["learning_rate"] > 0
    assert config["hyperparameters"]["batch_size"] > 0
    assert config["hyperparameters"]["epochs"] > 0
    assert config["data"]["train_size"] == 0.8
    assert config["data"]["val_size"] == 0.1
    assert config["data"]["test_size"] == 0.1


def test_split_logic_and_zero_leakage():
    train_df, val_df, test_df, meta = prepare_dataset(test_size=0.1, val_size=0.1, random_state=42)

    total = meta["total_samples"]
    assert len(train_df) + len(val_df) + len(test_df) == total

    # Check zero overlap between all partitions
    train_texts = set(train_df["clean_text"])
    val_texts = set(val_df["clean_text"])
    test_texts = set(test_df["clean_text"])

    assert len(train_texts.intersection(val_texts)) == 0
    assert len(train_texts.intersection(test_texts)) == 0
    assert len(val_texts.intersection(test_texts)) == 0


def test_evaluation_output_structure():
    y_true = [0, 1, 2, 3, 4]
    y_pred = [0, 1, 2, 3, 4]

    eval_out = compute_sentiment_metrics(y_true, y_pred)

    required_keys = {
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "weighted_f1",
        "per_class_precision",
        "per_class_recall",
        "per_class_f1",
        "mixed_class_evaluation",
        "unsupported_class_evaluation",
        "confusion_matrix",
    }
    assert required_keys.issubset(eval_out.keys())
