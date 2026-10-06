"""Dataset Loader and Splitter for Kollamo.ai NLP Pipeline.

Handles stratified partitioning, class distribution verification,
balanced class weights calculation, and strict data leakage prevention.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from ml.preprocessing.cleaner import clean_text

SENTIMENT_LABELS = ["positive", "negative", "neutral", "mixed", "unsupported"]
LABEL2ID = {label: idx for idx, label in enumerate(SENTIMENT_LABELS)}
ID2LABEL = {idx: label for label, idx in LABEL2ID.items()}


def load_raw_corpus(corpus_path: str = None) -> List[Dict[str, Any]]:
    """Loads raw dataset from JSON file."""
    if corpus_path is None:
        corpus_path = Path(__file__).parent / "corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def prepare_dataset(
    corpus_path: str = None,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Loads, cleans, and partitions corpus into train, val, test splits.

    Guarantees:
    - Stratified distribution across all 5 classes
    - Deterministic reproducibility via `random_state`
    - Zero data leakage between train, val, and test splits
    """
    raw_data = load_raw_corpus(corpus_path)
    df = pd.DataFrame(raw_data)

    # Validate required columns
    required_cols = {"id", "text", "label"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Corpus missing required columns: {required_cols - set(df.columns)}")

    # Preprocessing
    df["clean_text"] = df["text"].apply(clean_text)
    df["label_id"] = df["label"].map(LABEL2ID)

    if df["label_id"].isnull().any():
        unknown_labels = df[df["label_id"].isnull()]["label"].unique()
        raise ValueError(f"Encountered invalid labels in corpus: {unknown_labels}")

    # First split: train + val vs test
    train_val_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df["label_id"],
        random_state=random_state,
    )

    # Second split: train vs val
    val_relative_size = val_size / (1.0 - test_size)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=val_relative_size,
        stratify=train_val_df["label_id"],
        random_state=random_state,
    )

    # Assert Zero Data Leakage (check text overlap)
    train_texts = set(train_df["clean_text"])
    test_texts = set(test_df["clean_text"])
    val_texts = set(val_df["clean_text"])

    train_test_overlap = train_texts.intersection(test_texts)
    train_val_overlap = train_texts.intersection(val_texts)

    assert len(train_test_overlap) == 0, f"Data leakage detected! Overlapping texts: {train_test_overlap}"
    assert len(train_val_overlap) == 0, f"Data leakage detected! Overlapping texts: {train_val_overlap}"

    # Class distributions
    total_samples = len(df)
    class_counts = df["label"].value_counts().to_dict()
    n_classes = len(SENTIMENT_LABELS)

    # Calculate inverse frequency class weights: N / (C * count)
    class_weights = {}
    for label, idx in LABEL2ID.items():
        count = class_counts.get(label, 0)
        class_weights[idx] = float(total_samples / (n_classes * max(count, 1)))

    metadata = {
        "total_samples": total_samples,
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "class_counts": class_counts,
        "class_weights": class_weights,
        "random_state": random_state,
        "sentiment_labels": SENTIMENT_LABELS,
    }

    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True), metadata
