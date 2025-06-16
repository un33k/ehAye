"""Model-specific exception classes."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import EhAyeError


class ModelError(EhAyeError):
    """Base exception for model-related errors."""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        model_path: Optional[Union[str, Path]] = None,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, code, context, cause)
        self.model_name = model_name
        self.model_path = str(model_path) if model_path else None
        
        if model_name:
            self.context["model_name"] = model_name
        if self.model_path:
            self.context["model_path"] = self.model_path


class ModelNotFoundError(ModelError):
    """Raised when a requested model is not found."""
    
    def __init__(
        self, 
        model_name: str, 
        search_paths: Optional[List[Union[str, Path]]] = None
    ):
        message = f"Model '{model_name}' not found"
        context = {}
        if search_paths:
            context["search_paths"] = [str(p) for p in search_paths]
        
        super().__init__(message, model_name=model_name, context=context)


class ModelLoadError(ModelError):
    """Raised when model loading fails."""
    
    def __init__(
        self,
        model_name: str,
        reason: Optional[str] = None,
        model_path: Optional[Union[str, Path]] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Failed to load model '{model_name}'"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message,
            model_name=model_name,
            model_path=model_path,
            cause=cause
        )


class ModelDownloadError(ModelError):
    """Raised when model download fails."""
    
    def __init__(
        self,
        model_name: str,
        url: Optional[str] = None,
        bytes_downloaded: Optional[int] = None,
        total_size: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Failed to download model '{model_name}'"
        context = {}
        if url:
            context["url"] = url
        if bytes_downloaded is not None:
            context["bytes_downloaded"] = bytes_downloaded
        if total_size is not None:
            context["total_size"] = total_size
            if bytes_downloaded is not None:
                context["progress_percent"] = (bytes_downloaded / total_size) * 100
        
        super().__init__(
            message,
            model_name=model_name,
            context=context,
            cause=cause
        )


class ModelValidationError(ModelError):
    """Raised when model validation fails."""
    
    def __init__(
        self,
        model_name: str,
        validation_errors: List[str],
        model_path: Optional[Union[str, Path]] = None
    ):
        message = f"Model '{model_name}' failed validation"
        context = {
            "validation_errors": validation_errors,
            "error_count": len(validation_errors)
        }
        
        super().__init__(
            message,
            model_name=model_name,
            model_path=model_path,
            context=context
        )


class ModelCompatibilityError(ModelError):
    """Raised when model is not compatible with the current backend."""
    
    def __init__(
        self,
        model_name: str,
        backend_name: str,
        required_format: str,
        actual_format: Optional[str] = None,
        supported_formats: Optional[List[str]] = None
    ):
        message = f"Model '{model_name}' is not compatible with {backend_name} backend"
        context = {
            "backend_name": backend_name,
            "required_format": required_format,
        }
        
        if actual_format:
            context["actual_format"] = actual_format
        if supported_formats:
            context["supported_formats"] = supported_formats
        
        super().__init__(
            message,
            model_name=model_name,
            context=context
        )


class ModelSizeError(ModelError):
    """Raised when model size-related issues occur."""
    
    def __init__(
        self,
        model_name: str,
        model_size: Optional[int] = None,
        available_space: Optional[int] = None,
        required_memory: Optional[int] = None,
        available_memory: Optional[int] = None
    ):
        message = f"Model '{model_name}' size requirements not met"
        context = {}
        
        if model_size is not None:
            context["model_size_bytes"] = model_size
            context["model_size_mb"] = model_size / (1024 * 1024)
        
        if available_space is not None:
            context["available_space_bytes"] = available_space
            context["available_space_mb"] = available_space / (1024 * 1024)
        
        if required_memory is not None:
            context["required_memory_mb"] = required_memory
        
        if available_memory is not None:
            context["available_memory_mb"] = available_memory
        
        super().__init__(
            message,
            model_name=model_name,
            context=context
        )


class ModelCorruptionError(ModelError):
    """Raised when model files are corrupted."""
    
    def __init__(
        self,
        model_name: str,
        corrupted_files: List[str],
        model_path: Optional[Union[str, Path]] = None,
        checksum_mismatch: bool = False
    ):
        message = f"Model '{model_name}' has corrupted files"
        context = {
            "corrupted_files": corrupted_files,
            "corruption_count": len(corrupted_files),
            "checksum_mismatch": checksum_mismatch,
        }
        
        super().__init__(
            message,
            model_name=model_name,
            model_path=model_path,
            context=context
        )


class ModelPermissionError(ModelError):
    """Raised when model access permission issues occur."""
    
    def __init__(
        self,
        model_name: str,
        operation: str,
        model_path: Optional[Union[str, Path]] = None,
        cause: Optional[Exception] = None
    ):
        message = f"Permission denied for {operation} on model '{model_name}'"
        context = {"operation": operation}
        
        super().__init__(
            message,
            model_name=model_name,
            model_path=model_path,
            context=context,
            cause=cause
        )


class ModelRegistryError(ModelError):
    """Raised when model registry operations fail."""
    
    def __init__(
        self,
        message: str,
        registry_path: Optional[Union[str, Path]] = None,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if registry_path:
            context["registry_path"] = str(registry_path)
        if operation:
            context["operation"] = operation
        
        super().__init__(
            message,
            context=context,
            cause=cause
        )


class ModelVersionError(ModelError):
    """Raised when model version conflicts occur."""
    
    def __init__(
        self,
        model_name: str,
        required_version: str,
        available_version: Optional[str] = None,
        compatible_versions: Optional[List[str]] = None
    ):
        message = f"Model '{model_name}' version conflict"
        context = {
            "required_version": required_version,
        }
        
        if available_version:
            context["available_version"] = available_version
        if compatible_versions:
            context["compatible_versions"] = compatible_versions
        
        super().__init__(
            message,
            model_name=model_name,
            context=context
        )