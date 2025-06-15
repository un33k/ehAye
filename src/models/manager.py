"""Model management and download operations."""

import subprocess
from pathlib import Path
from typing import List, Optional

from ..core.config import get_config
from ..core.exceptions import ModelDownloadError, ModelError
from ..core.logging import get_logger
from .categories import ModelInfo, categorize_model
from .registry import model_registry

logger = get_logger("models.manager")


class ModelManager:
    """Manages model download, installation, and removal."""
    
    def __init__(self):
        self.config = get_config()
        self.registry = model_registry
    
    def download_model(self, model_id: str) -> ModelInfo:
        """Download and install a model."""
        logger.info(f"Downloading model: {model_id}")
        
        try:
            # Use huggingface-hub to download
            result = subprocess.run([
                "huggingface-cli", "download", model_id,
                "--cache-dir", str(self.config.paths.cache_dir / "huggingface"),
                "--local-dir", str(self.config.paths.models_dir / "downloaded" / model_id.replace("/", "_")),
                "--local-dir-use-symlinks", "False"
            ], 
            capture_output=True, 
            text=True, 
            timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise ModelDownloadError(f"Download failed: {result.stderr}")
            
            logger.info(f"Model {model_id} downloaded successfully")
            
            # Register the model
            model_info = self.registry.register_model(model_id)
            
            # Clean up old models if needed
            self._cleanup_if_needed()
            
            return model_info
            
        except subprocess.TimeoutExpired:
            raise ModelDownloadError(f"Download timeout for {model_id}")
        except Exception as e:
            raise ModelDownloadError(f"Download failed for {model_id}: {e}")
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model and clean up files."""
        logger.info(f"Removing model: {model_id}")
        
        try:
            # Remove from registry
            removed = self.registry.unregister_model(model_id)
            
            if not removed:
                logger.warning(f"Model {model_id} not found in registry")
                return False
            
            # Clean up downloaded files
            model_dir = self.config.paths.models_dir / "downloaded" / model_id.replace("/", "_")
            if model_dir.exists():
                import shutil
                shutil.rmtree(model_dir)
                logger.info(f"Removed model directory: {model_dir}")
            
            # Clean up cache
            self._cleanup_model_cache(model_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing model {model_id}: {e}")
            return False
    
    def list_available_models(self) -> List[str]:
        """List models available for download."""
        # This would typically query a model hub API
        # For now, return a curated list of popular MLX models
        return [
            "mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx",
            "mlx-community/phi-2-MLX",
            "mlx-community/CodeLlama-7b-Instruct-hf-4bit-mlx",
            "mlx-community/Llama-2-7b-chat-hf-4bit-mlx",
            "mlx-community/DeepSeek-R1-Distill-Qwen-1.5B-4bit",
            "mlx-community/Qwen2.5-Coder-7B-Instruct-4bit",
            "mlx-community/gemma-2-2b-it-4bit",
            "mlx-community/Meta-Llama-3-8B-Instruct-4bit",
        ]
    
    def search_available_models(self, query: str) -> List[str]:
        """Search available models by query."""
        available = self.list_available_models()
        query_lower = query.lower()
        
        return [
            model for model in available
            if query_lower in model.lower()
        ]
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get information about a model (installed or available)."""
        # First check if installed
        model_info = self.registry.find_model(model_id)
        if model_info:
            return model_info
        
        # If not installed, return categorized info
        if model_id in self.list_available_models():
            return categorize_model(model_id)
        
        return None
    
    def check_disk_space(self, required_gb: float = 5.0) -> bool:
        """Check if sufficient disk space is available."""
        try:
            import psutil
            
            disk = psutil.disk_usage(str(self.config.paths.models_dir))
            free_gb = disk.free / (1024**3)
            
            if free_gb < required_gb:
                logger.warning(f"Low disk space: {free_gb:.1f}GB free, {required_gb}GB required")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return True  # Assume OK if check fails
    
    def _cleanup_if_needed(self) -> None:
        """Clean up old models if cache size exceeded."""
        if not self.config.models.auto_cleanup:
            return
        
        try:
            cache_size_gb = self._calculate_cache_size()
            max_size_gb = self.config.performance.max_cache_size_gb
            
            if cache_size_gb > max_size_gb:
                logger.info(f"Cache size {cache_size_gb:.1f}GB exceeds limit {max_size_gb}GB")
                self._remove_oldest_models(cache_size_gb - max_size_gb)
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _calculate_cache_size(self) -> float:
        """Calculate total cache size in GB."""
        try:
            import os
            
            total_size = 0
            cache_dir = self.config.paths.cache_dir
            
            for root, dirs, files in os.walk(cache_dir):
                for file in files:
                    file_path = Path(root) / file
                    total_size += file_path.stat().st_size
            
            return total_size / (1024**3)
            
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0.0
    
    def _remove_oldest_models(self, target_gb: float) -> None:
        """Remove oldest models to free up space."""
        # This would implement LRU cleanup logic
        # For now, just log the intent
        logger.info(f"Would remove {target_gb:.1f}GB of old models")
    
    def _cleanup_model_cache(self, model_id: str) -> None:
        """Clean up cache files for a specific model."""
        try:
            # Clean up HuggingFace cache
            hf_cache = self.config.paths.cache_dir / "huggingface"
            model_cache_name = model_id.replace("/", "--")
            
            for cache_dir in hf_cache.glob(f"*{model_cache_name}*"):
                if cache_dir.is_dir():
                    import shutil
                    shutil.rmtree(cache_dir)
                    logger.debug(f"Removed cache: {cache_dir}")
                    
        except Exception as e:
            logger.error(f"Error cleaning cache for {model_id}: {e}")


# Global manager instance
model_manager = ModelManager()


def download_model(model_id: str) -> ModelInfo:
    """Download and install a model."""
    return model_manager.download_model(model_id)


def remove_model(model_id: str) -> bool:
    """Remove a model."""
    return model_manager.remove_model(model_id)


def list_available_models() -> List[str]:
    """List available models for download."""
    return model_manager.list_available_models()


def search_available_models(query: str) -> List[str]:
    """Search available models."""
    return model_manager.search_available_models(query)