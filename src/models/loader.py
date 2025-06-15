"""MLX model loading utilities."""

import time
from typing import Any, Optional, Tuple

from ..core.exceptions import ModelLoadError, ModelNotFoundError
from ..core.logging import get_logger
from .registry import find_model

logger = get_logger("models.loader")


class ModelLoader:
    """Handles MLX model loading operations."""
    
    def __init__(self):
        self._loaded_model: Optional[Tuple[Any, Any]] = None
        self._loaded_model_id: Optional[str] = None
    
    def load_model(self, model_id: str, force_reload: bool = False) -> Tuple[Any, Any]:
        """Load a model using MLX."""
        # Check if already loaded
        if (not force_reload and 
            self._loaded_model and 
            self._loaded_model_id == model_id):
            logger.debug(f"Model {model_id} already loaded")
            return self._loaded_model
        
        # Verify model is installed
        model_info = find_model(model_id)
        if not model_info:
            raise ModelNotFoundError(f"Model {model_id} not found in registry")
        
        logger.info(f"Loading model: {model_id}")
        start_time = time.time()
        
        try:
            from mlx_lm import load
            
            model, tokenizer = load(model_id)
            load_time = time.time() - start_time
            
            # Cache the loaded model
            self._loaded_model = (model, tokenizer)
            self._loaded_model_id = model_id
            
            logger.info(f"Model loaded successfully in {load_time:.2f}s")
            return model, tokenizer
            
        except ImportError as e:
            raise ModelLoadError(f"MLX not available: {e}")
        except Exception as e:
            raise ModelLoadError(f"Failed to load model {model_id}: {e}")
    
    def unload_model(self) -> None:
        """Unload the currently loaded model."""
        if self._loaded_model:
            logger.info(f"Unloading model: {self._loaded_model_id}")
            self._loaded_model = None
            self._loaded_model_id = None
            
            # Force garbage collection
            import gc
            gc.collect()
    
    def get_loaded_model(self) -> Optional[Tuple[str, Any, Any]]:
        """Get currently loaded model info."""
        if self._loaded_model and self._loaded_model_id:
            return (self._loaded_model_id, *self._loaded_model)
        return None
    
    def is_model_loaded(self, model_id: Optional[str] = None) -> bool:
        """Check if a model is loaded."""
        if model_id:
            return self._loaded_model_id == model_id
        return self._loaded_model is not None
    
    def estimate_memory_usage(self, model_id: str) -> Optional[float]:
        """Estimate memory usage for a model."""
        model_info = find_model(model_id)
        if not model_info or not model_info.size_gb:
            return None
        
        # Add overhead for tokenizer and framework
        return model_info.size_gb * 1.2
    
    def validate_model_compatibility(self, model_id: str) -> bool:
        """Validate that model is compatible with MLX."""
        try:
            from mlx_lm import load
            
            # Try to get model info without loading
            model_info = find_model(model_id)
            if not model_info:
                return False
            
            # Basic MLX compatibility check
            if "mlx" not in model_id.lower():
                logger.warning(f"Model {model_id} may not be MLX-optimized")
            
            return True
            
        except ImportError:
            logger.error("MLX not available")
            return False
        except Exception as e:
            logger.error(f"Model compatibility check failed: {e}")
            return False


# Global loader instance
model_loader = ModelLoader()


def load_model(model_id: str, force_reload: bool = False) -> Tuple[Any, Any]:
    """Load a model using MLX."""
    return model_loader.load_model(model_id, force_reload)


def unload_model() -> None:
    """Unload the currently loaded model."""
    model_loader.unload_model()


def get_loaded_model() -> Optional[Tuple[str, Any, Any]]:
    """Get currently loaded model info."""
    return model_loader.get_loaded_model()


def is_model_loaded(model_id: Optional[str] = None) -> bool:
    """Check if a model is loaded."""
    return model_loader.is_model_loaded(model_id)