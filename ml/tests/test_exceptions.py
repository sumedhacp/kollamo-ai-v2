"""Unit Tests for ML Custom Exception Hierarchy."""

import pytest
from ml.exceptions import (
    KollamoMLException,
    ModelLoadingError,
    InferenceError,
    PreprocessingError,
    ConfigurationError,
    UnsupportedInputError,
)


def test_exception_hierarchy():
    assert issubclass(ModelLoadingError, KollamoMLException)
    assert issubclass(InferenceError, KollamoMLException)
    assert issubclass(PreprocessingError, KollamoMLException)
    assert issubclass(ConfigurationError, KollamoMLException)
    assert issubclass(UnsupportedInputError, KollamoMLException)


def test_exception_message_and_details():
    exc = ModelLoadingError("Model file not found", details={"path": "/invalid/path"})
    assert str(exc) == "Model file not found"
    assert exc.message == "Model file not found"
    assert exc.details == {"path": "/invalid/path"}
