"""Base exception classes for ehAye."""

from typing import Any, Dict, Optional


class EhAyeError(Exception):
    """Base exception for all ehAye errors."""
    
    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.context = context or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """String representation of the error."""
        result = self.message
        if self.code and self.code != self.__class__.__name__:
            result = f"[{self.code}] {result}"
        return result
    
    def __repr__(self) -> str:
        """Detailed representation of the error."""
        parts = [f"message='{self.message}'"]
        if self.code:
            parts.append(f"code='{self.code}'")
        if self.context:
            parts.append(f"context={self.context}")
        if self.cause:
            parts.append(f"cause={self.cause!r}")
        
        return f"{self.__class__.__name__}({', '.join(parts)})"
    
    def with_context(self, **kwargs) -> 'EhAyeError':
        """Add context information to the error."""
        self.context.update(kwargs)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'code': self.code,
            'context': self.context,
            'cause': str(self.cause) if self.cause else None,
        }


class EhAyeWarning(UserWarning):
    """Base warning class for ehAye."""
    
    def __init__(self, message: str, category: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.category = category or "general"


class ConfigurationError(EhAyeError):
    """Raised when there's a configuration error."""
    pass


class EnvironmentError(EhAyeError):
    """Raised when environment setup fails."""
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


class NetworkError(EhAyeError):
    """Raised when network operations fail."""
    pass


class SecurityError(EhAyeError):
    """Raised when security-related operations fail."""
    pass


class PermissionError(EhAyeError):
    """Raised when permission-related operations fail."""
    pass