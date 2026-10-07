"""Canonical Phase 2 ML Exceptions."""


class KollamoMLException(Exception):
    """Base exception for all Phase 2 ML pipeline errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ModelNotReadyError(KollamoMLException):
    """Raised when the fine-tuned 5-class model checkpoint has not yet been trained or provided."""

    def __init__(
        self,
        message: str = "The Kollamo sentiment model is not available for inference.",
        details: dict = None,
    ):
        super().__init__(message, details=details or {"status": "MODEL_NOT_READY"})


class ModelUnavailableError(KollamoMLException):
    """Raised when the model should exist but cannot currently be loaded or accessed."""

    def __init__(
        self,
        message: str = "The Kollamo sentiment model is currently unavailable.",
        details: dict = None,
    ):
        super().__init__(message, details=details or {"status": "MODEL_UNAVAILABLE"})


class InferenceError(KollamoMLException):
    """Raised when model inference execution fails."""

    def __init__(
        self,
        message: str = "Sentiment inference failed.",
        details: dict = None,
    ):
        super().__init__(message, details=details or {"status": "INFERENCE_ERROR"})
