"""Google MuRIL Multilingual Sentiment Neural Classifier.

Architecture:
Input (text)
  -> MuRIL WordPiece Tokenizer
  -> MuRIL Transformer Encoder (google/muril-base-cased, 768 hidden)
  -> Mean / [CLS] Pooling
  -> Dropout (p=0.2)
  -> Classification Head (Linear 768 -> 5)
  -> 5-Class Prediction & Softmax Probabilities
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer, AutoConfig
from ml.models.taxonomy import (
    SENTIMENT_LABELS,
    SENTIMENT_CLASSES,
    ID2LABEL,
    ID2CLASS,
    LABEL2ID,
)

# Authoritative Base Pretrained Model from Hugging Face
DEFAULT_BASE_CHECKPOINT = "google/muril-base-cased"


class MurilClassificationHead(nn.Module):
    """Linear classification head with dropout and layer norm."""

    def __init__(self, hidden_size: int = 768, num_classes: int = 5, dropout_prob: float = 0.2):
        super().__init__()
        self.dropout = nn.Dropout(dropout_prob)
        self.layer_norm = nn.LayerNorm(hidden_size)
        self.classifier = nn.Linear(hidden_size, num_classes)

    def forward(self, pooled_features: torch.Tensor) -> torch.Tensor:
        x = self.layer_norm(pooled_features)
        x = self.dropout(x)
        logits = self.classifier(x)
        return logits


class MurilSentimentClassifier(nn.Module):
    """Full Neural Sentiment Classifier wrapping Google MuRIL."""

    def __init__(
        self,
        model_name: str = "google/muril-base-cased",
        num_classes: int = 5,
        dropout_prob: float = 0.2,
        pretrained: bool = True,
    ):
        super().__init__()
        self.model_name = model_name
        self.num_classes = num_classes

        if pretrained:
            try:
                self.encoder = AutoModel.from_pretrained(model_name)
                hidden_size = self.encoder.config.hidden_size
            except Exception:
                # Fallback to local config or standard BERT config if offline
                config = AutoConfig.from_pretrained(model_name)
                self.encoder = AutoModel.from_config(config)
                hidden_size = config.hidden_size
        else:
            config = AutoConfig.from_pretrained(model_name)
            self.encoder = AutoModel.from_config(config)
            hidden_size = config.hidden_size

        self.head = MurilClassificationHead(
            hidden_size=hidden_size,
            num_classes=num_classes,
            dropout_prob=dropout_prob,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Forward pass through MuRIL encoder and classification head.

        Returns:
            logits: Tensor of shape (batch_size, num_classes)
        """
        encoder_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
        }
        if token_type_ids is not None:
            encoder_kwargs["token_type_ids"] = token_type_ids

        outputs = self.encoder(**encoder_kwargs)

        # Use pooler_output if present, otherwise mean pool over sequence dimension
        if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
            pooled = outputs.pooler_output
        else:
            # Masked mean pooling
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(outputs.last_hidden_state.size()).float()
            sum_embeddings = torch.sum(outputs.last_hidden_state * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            pooled = sum_embeddings / sum_mask

        logits = self.head(pooled)
        return logits

    def predict_probabilities(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Returns normalized softmax probabilities (batch_size, num_classes)."""
        self.eval()
        with torch.no_grad():
            logits = self.forward(input_ids, attention_mask)
            probabilities = torch.softmax(logits, dim=-1)
        return probabilities

    def save_weights(self, output_dir: str) -> None:
        """Saves model weights and configuration."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), out_path / "muril_classifier.pt")

    def load_weights(self, weights_path: str, device: str = "cpu") -> None:
        """Loads state dictionary weights."""
        state_dict = torch.load(weights_path, map_location=device)
        self.load_state_dict(state_dict)

    @classmethod
    def from_pretrained(
        cls,
        model_name_or_path: str,
        num_classes: int = 5,
        dropout_prob: float = 0.2,
        device: str = "cpu",
    ) -> "MurilSentimentClassifier":
        """Factory method to load classifier from directory, checkpoint file, or pretrained backbone."""
        path = Path(model_name_or_path)
        weights_file = None

        if path.is_file() and path.suffix in (".pt", ".bin"):
            weights_file = path
            base_model_name = "google/muril-base-cased"
        elif path.is_dir():
            for candidate in ("muril_classifier.pt", "pytorch_model.bin", "model.pt"):
                if (path / candidate).exists():
                    weights_file = path / candidate
                    break
            base_model_name = str(path) if (path / "config.json").exists() else "google/muril-base-cased"
        else:
            base_model_name = model_name_or_path

        model = cls(
            model_name=base_model_name,
            num_classes=num_classes,
            dropout_prob=dropout_prob,
            pretrained=True if not weights_file else False,
        )

        if weights_file and weights_file.exists():
            model.load_weights(str(weights_file), device=device)

        model.to(device)
        return model


# Authoritative alias for casing consistency across repository
MuRILSentimentClassifier = MurilSentimentClassifier
