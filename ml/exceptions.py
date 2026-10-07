"""Custom Exceptions for Kollamo.ai ML/NLP Pipeline."""


class KollamoMLException(Exception):
    """Base exception for all Kollamo.ai ML pipeline errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ModelLoadingError(KollamoMLException):
    """Raised when model weights, architecture, or tokenizer fails to load."""
    pass


class ModelNotTrainedError(ModelLoadingError):
    """Raised when attempting production inference with an untrained base model or missing fine-tuned checkpoint."""

    def __init__(self, message: str = "Trained Kollamo checkpoint not found. Status: MODEL_NOT_TRAINED", details: dict = None):
        super().__init__(message, details=details or {"status": "MODEL_NOT_TRAINED"})


class InferenceError(KollamoMLException):
    """Raised when an unrecoverable error occurs during model forward pass."""
    pass


class PreprocessingError(KollamoMLException):
    """Raised when text sanitization, normalization, or script analysis fails."""
    pass


class ConfigurationError(KollamoMLException):
    """Raised when ML configuration or hyperparameters are invalid or missing."""
    pass


class UnsupportedInputError(KollamoMLException):
    """Raised when input text cannot be processed or represents unsupported content."""
    pass
