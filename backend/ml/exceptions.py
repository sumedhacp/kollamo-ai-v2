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


class ModelLoadingError(ModelUnavailableError):
    """Raised when model weights, architecture, or tokenizer fails to load."""
    pass


class ModelNotTrainedError(ModelNotReadyError):
    """Raised when attempting production inference with an untrained base model or missing fine-tuned checkpoint."""

    def __init__(self, message: str = "Trained Kollamo checkpoint not found. Status: MODEL_NOT_TRAINED", details: dict = None):
        super().__init__(message, details=details or {"status": "MODEL_NOT_TRAINED"})


class ConfigurationError(KollamoMLException):
    """Raised when ML configuration or hyperparameters are invalid or missing."""
    pass


class PreprocessingError(KollamoMLException):
    """Raised when text sanitization, normalization, or script analysis fails."""
    pass


class UnsupportedInputError(KollamoMLException):
    """Raised when input text cannot be processed or represents unsupported content."""
    pass
