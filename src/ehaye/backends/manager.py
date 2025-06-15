"""Backend manager for handling multiple LLM backends."""

from typing import Dict, List, Optional
from ..core.config import get_config
from ..core.logging import get_logger
from .base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig
from .ollama_backend import OllamaBackend
from .mlx_backend import MLXBackend

logger = get_logger("backends.manager")


class BackendManager:
    """Manages multiple LLM backends."""
    
    def __init__(self):
        self._backends: Dict[str, BaseBackend] = {}
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize available backends."""
        # Initialize Ollama backend
        ollama = OllamaBackend()
        if ollama.is_available():
            self._backends["ollama"] = ollama
            logger.info("Ollama backend initialized")
        else:
            logger.warning("Ollama backend not available")
        
        # Initialize MLX backend
        mlx = MLXBackend()
        if mlx.is_available():
            self._backends["mlx"] = mlx
            logger.info("MLX backend initialized")
        else:
            logger.warning("MLX backend not available")
    
    def get_backend(self, name: Optional[str] = None) -> BaseBackend:
        """Get a backend by name or return the default."""
        if name is None:
            config = get_config()
            name = config.models.default_backend
        
        if name not in self._backends:
            available = list(self._backends.keys())
            if not available:
                raise RuntimeError("No backends available")
            
            logger.warning(f"Backend '{name}' not available, using '{available[0]}'")
            name = available[0]
        
        return self._backends[name]
    
    def list_backends(self) -> List[str]:
        """List available backend names."""
        return list(self._backends.keys())
    
    def is_backend_available(self, name: str) -> bool:
        """Check if a backend is available."""
        return name in self._backends
    
    def list_all_models(self, backend: Optional[str] = None) -> Dict[str, List[ModelInfo]]:
        """List models from all backends or a specific backend."""
        if backend:
            if backend in self._backends:
                return {backend: self._backends[backend].list_models()}
            else:
                return {}
        
        result = {}
        for name, backend_obj in self._backends.items():
            try:
                models = backend_obj.list_models()
                result[name] = models
            except Exception as e:
                logger.error(f"Error listing models from {name}: {e}")
                result[name] = []
        
        return result
    
    def search_all_models(self, query: Optional[str] = None, backend: Optional[str] = None) -> Dict[str, List[ModelInfo]]:
        """Search models from all backends or a specific backend."""
        if backend:
            if backend in self._backends:
                return {backend: self._backends[backend].search_models(query)}
            else:
                return {}
        
        result = {}
        for name, backend_obj in self._backends.items():
            try:
                models = backend_obj.search_models(query)
                result[name] = models
            except Exception as e:
                logger.error(f"Error searching models from {name}: {e}")
                result[name] = []
        
        return result


# Global backend manager instance
_backend_manager = None


def get_backend_manager() -> BackendManager:
    """Get the global backend manager."""
    global _backend_manager
    if _backend_manager is None:
        _backend_manager = BackendManager()
    return _backend_manager


def get_backend(name: Optional[str] = None) -> BaseBackend:
    """Get a backend by name or return the default."""
    return get_backend_manager().get_backend(name)