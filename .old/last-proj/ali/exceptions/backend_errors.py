"""Backend-specific exception classes."""

from typing import Any, Dict, Optional

from .base import EhAyeError


class BackendError(EhAyeError):
    """Base exception for backend-related errors."""
    
    def __init__(
        self,
        message: str,
        backend_name: Optional[str] = None,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, code, context, cause)
        self.backend_name = backend_name
        if backend_name:
            self.context["backend"] = backend_name


class BackendNotAvailableError(BackendError):
    """Raised when a backend is not available or not installed."""
    
    def __init__(self, backend_name: str, reason: Optional[str] = None):
        message = f"Backend '{backend_name}' is not available"
        if reason:
            message += f": {reason}"
        super().__init__(message, backend_name=backend_name)


class BackendConnectionError(BackendError):
    """Raised when unable to connect to a backend service."""
    
    def __init__(
        self, 
        backend_name: str, 
        endpoint: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Failed to connect to {backend_name} backend"
        if endpoint:
            message += f" at {endpoint}"
        
        context = {}
        if endpoint:
            context["endpoint"] = endpoint
        
        super().__init__(message, backend_name=backend_name, context=context, cause=cause)


class BackendTimeoutError(BackendError):
    """Raised when a backend operation times out."""
    
    def __init__(
        self, 
        backend_name: str, 
        operation: str,
        timeout_seconds: float,
        cause: Optional[Exception] = None
    ):
        message = f"{backend_name} backend timed out during {operation} (timeout: {timeout_seconds}s)"
        context = {
            "operation": operation,
            "timeout_seconds": timeout_seconds,
        }
        super().__init__(message, backend_name=backend_name, context=context, cause=cause)


class BackendResponseError(BackendError):
    """Raised when a backend returns an invalid response."""
    
    def __init__(
        self,
        backend_name: str,
        expected_format: str,
        actual_response: Any,
        cause: Optional[Exception] = None
    ):
        message = f"{backend_name} backend returned invalid response format"
        context = {
            "expected_format": expected_format,
            "actual_response": str(actual_response)[:500],  # Truncate long responses
        }
        super().__init__(message, backend_name=backend_name, context=context, cause=cause)


class OllamaError(BackendError):
    """Ollama-specific errors."""
    
    def __init__(
        self,
        message: str,
        api_error: Optional[str] = None,
        status_code: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if api_error:
            context["api_error"] = api_error
        if status_code:
            context["status_code"] = status_code
        
        super().__init__(message, backend_name="ollama", context=context, cause=cause)


class OllamaServiceError(OllamaError):
    """Raised when Ollama service is not running or accessible."""
    
    def __init__(self, endpoint: str = "http://localhost:11434"):
        message = f"Ollama service not accessible at {endpoint}"
        super().__init__(
            message,
            context={"endpoint": endpoint, "suggestion": "Start Ollama with 'ollama serve'"}
        )


class OllamaModelNotFoundError(OllamaError):
    """Raised when a requested model is not available in Ollama."""
    
    def __init__(self, model_name: str):
        message = f"Model '{model_name}' not found in Ollama"
        super().__init__(
            message,
            context={
                "model_name": model_name,
                "suggestion": f"Pull the model with 'ollama pull {model_name}'"
            }
        )


class MLXError(BackendError):
    """MLX-specific errors."""
    
    def __init__(
        self,
        message: str,
        mlx_error: Optional[str] = None,
        metal_available: Optional[bool] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if mlx_error:
            context["mlx_error"] = mlx_error
        if metal_available is not None:
            context["metal_available"] = metal_available
        
        super().__init__(message, backend_name="mlx", context=context, cause=cause)


class MLXNotAvailableError(MLXError):
    """Raised when MLX is not available (not on Apple Silicon)."""
    
    def __init__(self, platform: str, architecture: str):
        message = "MLX backend is only available on Apple Silicon Macs"
        context = {
            "platform": platform,
            "architecture": architecture,
            "suggestion": "Use Ollama backend instead"
        }
        super().__init__(message, context=context)


class MLXMemoryError(MLXError):
    """Raised when MLX runs out of memory."""
    
    def __init__(self, required_memory: Optional[int] = None, available_memory: Optional[int] = None):
        message = "Insufficient memory for MLX operation"
        context = {}
        if required_memory:
            context["required_memory_mb"] = required_memory
        if available_memory:
            context["available_memory_mb"] = available_memory
        
        super().__init__(message, context=context)


class MLXModelFormatError(MLXError):
    """Raised when MLX model format is incorrect."""
    
    def __init__(self, model_path: str, expected_format: str):
        message = f"Model format error: expected {expected_format}"
        context = {
            "model_path": model_path,
            "expected_format": expected_format,
            "suggestion": "Convert model to MLX format"
        }
        super().__init__(message, context=context)