from pathlib import Path

_root_ml_inf = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "inference"
if _root_ml_inf.exists() and str(_root_ml_inf) not in __path__:
    __path__.append(str(_root_ml_inf))

from .service import (
    SentimentInferenceService,
    SentimentInferenceProtocol,
    ModelReadiness,
)

__all__ = [
    "SentimentInferenceService",
    "SentimentInferenceProtocol",
    "ModelReadiness",
]
