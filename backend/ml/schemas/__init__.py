from pathlib import Path

_root_ml_schemas = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "schemas"
if _root_ml_schemas.exists() and str(_root_ml_schemas) not in __path__:
    __path__.append(str(_root_ml_schemas))

from .prediction import (
    SentimentPrediction,
    SentimentProbabilities,
)

__all__ = ["SentimentPrediction", "SentimentProbabilities"]

