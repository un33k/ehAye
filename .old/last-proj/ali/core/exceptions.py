"""Custom exceptions for ehAye Local."""


class EhAyeError(Exception):
    """Base exception for all ehAye Local errors."""
    
    def __init__(self, message: str, code: str = None):
        super().__init__(message)
        self.message = message
        self.code = code


class ConfigurationError(EhAyeError):
    """Raised when there's a configuration error."""
    pass


class EnvironmentError(EhAyeError):
    """Raised when environment setup fails."""
    pass


class ModelError(EhAyeError):
    """Base exception for model-related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Raised when a requested model is not found."""
    pass


class ModelLoadError(ModelError):
    """Raised when model loading fails."""
    pass


class ModelDownloadError(ModelError):
    """Raised when model download fails."""
    pass


class SystemResourceError(EhAyeError):
    """Raised when system resources are insufficient."""
    pass


class VirtualEnvironmentError(EnvironmentError):
    """Raised when virtual environment validation fails."""
    pass


class GPUError(EhAyeError):
    """Raised when GPU-related operations fail."""
    pass


class BenchmarkError(EhAyeError):
    """Raised when benchmark operations fail."""
    pass


class CLIError(EhAyeError):
    """Raised when CLI operations fail."""
    pass