"""Enhanced exception handling for ehAye."""

from .base import EhAyeError, EhAyeWarning
from .backend_errors import (
    BackendError, 
    BackendNotAvailableError,
    BackendConnectionError,
    BackendTimeoutError,
    OllamaError,
    MLXError
)
from .model_errors import (
    ModelError,
    ModelNotFoundError, 
    ModelLoadError,
    ModelDownloadError,
    ModelValidationError,
    ModelCompatibilityError
)
from .cli_errors import (
    CLIError,
    CommandError,
    ArgumentError,
    ValidationError
)
from .utils import (
    handle_exception,
    format_exception,
    create_error_context
)

__all__ = [
    # Base exceptions
    "EhAyeError",
    "EhAyeWarning",
    
    # Backend exceptions
    "BackendError",
    "BackendNotAvailableError", 
    "BackendConnectionError",
    "BackendTimeoutError",
    "OllamaError",
    "MLXError",
    
    # Model exceptions
    "ModelError",
    "ModelNotFoundError",
    "ModelLoadError", 
    "ModelDownloadError",
    "ModelValidationError",
    "ModelCompatibilityError",
    
    # CLI exceptions
    "CLIError",
    "CommandError",
    "ArgumentError", 
    "ValidationError",
    
    # Utilities
    "handle_exception",
    "format_exception",
    "create_error_context",
]