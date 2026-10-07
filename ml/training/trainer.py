"""Trainer Module for Fine-Tuning Google MuRIL on Multilingual Comments."""

import os
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from ml.models.taxonomy import SENTIMENT_LABELS, LABEL2ID, ID2LABEL, ID2CLASS, SENTIMENT_CLASSES
from ml.models.muril_classifier import MurilSentimentClassifier
from ml.evaluation.metrics import compute_sentiment_metrics, save_experiment_report
from ml.evaluation.error_analyzer import run_error_analysis
from ml.exceptions import ModelLoadingError


class CommentSentimentDataset(Dataset):
    """PyTorch Dataset wrapper for tokenized Malayalam & Manglish comments."""

    def __init__(self, texts: list, labels: list, tokenizer: Any, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        item = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }
        if "token_type_ids" in encoding:
            item["token_type_ids"] = encoding["token_type_ids"].squeeze(0)

        return item


class MurilTrainer:
    """Trainer orchestrator for MuRIL fine-tuning."""

    def __init__(
        self,
        config: Dict[str, Any],
        device: Optional[str] = None,
    ):
        self.config = config
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Set seeds for strict reproducibility
        seed = config.get("hyperparameters", {}).get("seed", 42)
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        # Official base pretrained model: google/muril-base-cased
        self.model_name = config.get("model_architecture", "google/muril-base-cased")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        except Exception as e:
            raise ModelLoadingError(
                f"Failed to load official MuRIL tokenizer from '{self.model_name}'. "
                f"Per Phase 2 rules, mBERT/XLM-R substitution is strictly forbidden: {e}"
            ) from e

        self.model = MurilSentimentClassifier(
            model_name=self.model_name,
            num_classes=config.get("hyperparameters", {}).get("num_classes", 5),
            dropout_prob=config.get("hyperparameters", {}).get("dropout_prob", 0.2),
            pretrained=True,
        ).to(self.device)

    def train(
        self,
        train_df,
        val_df,
        test_df,
        dataset_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Executes full training, checkpointing, and evaluation loop."""
        hp = self.config.get("hyperparameters", {})
        batch_size = hp.get("batch_size", 16)
        max_length = hp.get("max_length", 128)
        epochs = hp.get("epochs", 3)
        lr = float(hp.get("learning_rate", 2e-5))
        weight_decay = float(hp.get("weight_decay", 0.01))
        save_dir = Path(self.config.get("paths", {}).get("save_dir", "ml/models/saved_weights/kollamo-muril-sentiment-5class"))
        save_dir.mkdir(parents=True, exist_ok=True)

        # Datasets & DataLoaders
        train_dataset = CommentSentimentDataset(train_df["clean_text"].tolist(), train_df["label_id"].tolist(), self.tokenizer, max_length)
        val_dataset = CommentSentimentDataset(val_df["clean_text"].tolist(), val_df["label_id"].tolist(), self.tokenizer, max_length)
        test_dataset = CommentSentimentDataset(test_df["clean_text"].tolist(), test_df["label_id"].tolist(), self.tokenizer, max_length)

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

        # Weighted loss if enabled
        if self.config.get("loss", {}).get("use_weighted_loss", True):
            weights_dict = dataset_meta.get("class_weights", {})
            weight_tensor = torch.tensor([weights_dict.get(i, 1.0) for i in range(5)], dtype=torch.float).to(self.device)
            criterion = nn.CrossEntropyLoss(weight=weight_tensor)
        else:
            criterion = nn.CrossEntropyLoss()

        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        total_steps = len(train_loader) * epochs
        warmup_steps = int(total_steps * hp.get("warmup_ratio", 0.1))
        scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

        best_val_f1 = -1.0
        best_checkpoint_path = save_dir / "best_model.pt"

        print(f"Beginning training on device '{self.device}' for {epochs} epochs ({total_steps} steps)...")

        for epoch in range(1, epochs + 1):
            self.model.train()
            train_loss = 0.0

            for batch in train_loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["label"].to(self.device)

                optimizer.zero_grad()
                logits = self.model(input_ids, attention_mask)
                loss = criterion(logits, labels)
                loss.backward()

                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                scheduler.step()

                train_loss += loss.item()

            avg_train_loss = train_loss / max(len(train_loader), 1)

            # Validation phase
            val_loss, val_metrics = self._evaluate_loader(val_loader, criterion)
            print(f"Epoch {epoch}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Macro F1: {val_metrics['macro_f1']:.4f}")

            if val_metrics["macro_f1"] > best_val_f1:
                best_val_f1 = val_metrics["macro_f1"]
                torch.save(self.model.state_dict(), best_checkpoint_path)

        # Load best checkpoint for final test evaluation
        if best_checkpoint_path.exists():
            self.model.load_state_dict(torch.load(best_checkpoint_path, map_location=self.device))

        test_loss, test_metrics = self._evaluate_loader(test_loader, criterion)

        # Run linguistic error analysis on probes
        def predict_probe_fn(texts):
            self.model.eval()
            inputs = self.tokenizer(texts, max_length=max_length, padding=True, truncation=True, return_tensors="pt").to(self.device)
            with torch.no_grad():
                logits = self.model(inputs["input_ids"], inputs["attention_mask"])
                preds = torch.argmax(logits, dim=-1).cpu().numpy().tolist()
            return [ID2LABEL[p] for p in preds]

        error_report = run_error_analysis(predict_probe_fn)
        test_metrics["error_analysis"] = error_report
        test_metrics["validation_loss"] = test_loss

        # Save metrics report
        metrics_out = self.config.get("paths", {}).get("metrics_output", "ml/evaluation/reports/muril_metrics.json")
        save_experiment_report(
            metrics=test_metrics,
            experiment_name=self.config.get("experiment_name", "muril_multilingual_sentiment"),
            hyperparameters=hp,
            dataset_metadata=dataset_meta,
            output_path=str(Path(metrics_out)),
            git_commit_sha="cf91968",
        )

        return test_metrics

    def _evaluate_loader(self, loader: DataLoader, criterion: nn.Module) -> Tuple[float, Dict[str, Any]]:
        self.model.eval()
        total_loss = 0.0
        all_preds = []
        all_labels = []

        start_time = time.time()
        with torch.no_grad():
            for batch in loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["label"].to(self.device)

                logits = self.model(input_ids, attention_mask)
                loss = criterion(logits, labels)
                total_loss += loss.item()

                preds = torch.argmax(logits, dim=-1).cpu().numpy().tolist()
                all_preds.extend(preds)
                all_labels.extend(labels.cpu().numpy().tolist())

        total_samples = max(len(all_labels), 1)
        inference_time_ms = ((time.time() - start_time) / total_samples) * 1000.0
        avg_loss = total_loss / max(len(loader), 1)

        metrics = compute_sentiment_metrics(all_labels, all_preds, val_loss=avg_loss, inference_time_ms=inference_time_ms)
        return avg_loss, metrics
