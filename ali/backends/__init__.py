"""Backend management for LLM providers."""

from .base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig
from .manager import BackendManager, get_backend_manager, get_backend
from .ollama_backend import OllamaBackend
from .mlx_backend import MLXBackend

__all__ = [
    "BaseBackend",
    "ModelInfo", 
    "ChatMessage",
    "GenerationConfig",
    "BackendManager",
    "get_backend_manager",
    "get_backend",
    "OllamaBackend",
    "MLXBackend",
]