"""MLX backend implementation."""

from typing import List, Dict, Optional, Iterator
from pathlib import Path

from ..core.logging import get_logger
from ..models.manager import download_model, list_available_models, remove_model
from ..models.registry import get_installed_models, search_models
from .base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig

logger = get_logger("backends.mlx")


class MLXBackend(BaseBackend):
    """MLX backend for Apple Silicon optimized LLM operations."""
    
    def __init__(self):
        self.loaded_models = {}
        
    def is_available(self) -> bool:
        """Check if MLX is available."""
        try:
            import mlx.core as mx
            return True
        except ImportError:
            return False
    
    def list_models(self) -> List[ModelInfo]:
        """List all installed models."""
        try:
            models = get_installed_models()
            return [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    size=model.size_params,
                    description=f"{model.category} model",
                    family=model.category,
                    format="mlx",
                    installed=True
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Failed to list MLX models: {e}")
            return []
    
    def search_models(self, query: Optional[str] = None) -> List[ModelInfo]:
        """Search available models for download."""
        try:
            if query:
                # Use existing search functionality
                models = search_models(query=query)
                return [
                    ModelInfo(
                        id=model.id,
                        name=model.name,
                        size=model.size_params,
                        description=f"{model.category} model",
                        family=model.category,
                        format="mlx",
                        installed=False
                    )
                    for model in models
                ]
            else:
                # Get all available models
                model_ids = list_available_models()
                from ..models.categories import categorize_model
                
                return [
                    ModelInfo(
                        id=model_id,
                        name=categorize_model(model_id).display_name,
                        size=categorize_model(model_id).size_params,
                        description=f"{categorize_model(model_id).category} model",
                        family=categorize_model(model_id).category,
                        format="mlx",
                        installed=False
                    )
                    for model_id in model_ids
                ]
        except Exception as e:
            logger.error(f"Failed to search MLX models: {e}")
            return []
    
    def download_model(self, model_id: str, progress_callback: Optional[callable] = None) -> ModelInfo:
        """Download and install a model."""
        try:
            model_info = download_model(model_id)
            return ModelInfo(
                id=model_info.id,
                name=model_info.name,
                size=model_info.size_params,
                description=f"{model_info.category} model",
                family=model_info.category,
                format="mlx",
                installed=True
            )
        except Exception as e:
            logger.error(f"Failed to download MLX model {model_id}: {e}")
            raise
    
    def remove_model(self, model_id: str) -> bool:
        """Remove an installed model."""
        try:
            return remove_model(model_id)
        except Exception as e:
            logger.error(f"Failed to remove MLX model {model_id}: {e}")
            return False
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed information about a model."""
        try:
            models = get_installed_models()
            for model in models:
                if model.id == model_id:
                    return ModelInfo(
                        id=model.id,
                        name=model.name,
                        size=model.size_params,
                        description=f"{model.category} model - {model.size_gb:.1f}GB" if model.size_gb else f"{model.category} model",
                        parameters=model.size_params,
                        family=model.category,
                        format="mlx",
                        installed=True
                    )
            return None
        except Exception as e:
            logger.error(f"Failed to get MLX model info for {model_id}: {e}")
            return None
    
    def generate(
        self, 
        model_id: str, 
        messages: List[ChatMessage], 
        config: GenerationConfig
    ) -> Iterator[str]:
        """Generate text response from the model."""
        try:
            # Import MLX modules
            from ..llm.generation import generate_response
            from ..llm.prompts import format_messages
            
            # Format messages for the model
            prompt = format_messages(messages, model_id)
            
            # Generate response
            if config.stream:
                # Use existing streaming functionality
                from ..llm.streaming import stream_response
                for chunk in stream_response(model_id, prompt, config.temperature, config.max_tokens):
                    yield chunk
            else:
                # Non-streaming generation
                response = generate_response(model_id, prompt, config.temperature, config.max_tokens)
                yield response
                
        except Exception as e:
            logger.error(f"Error generating text with MLX: {e}")
            yield f"Error: {e}"
    
    def load_model(self, model_id: str) -> bool:
        """Load a model into memory for inference."""
        try:
            if model_id in self.loaded_models:
                return True
                
            # Use existing model loading functionality
            from ..models.loader import load_model
            model, tokenizer = load_model(model_id)
            
            self.loaded_models[model_id] = {
                'model': model,
                'tokenizer': tokenizer
            }
            
            logger.info(f"Successfully loaded MLX model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load MLX model {model_id}: {e}")
            return False
    
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        try:
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]
                logger.info(f"Unloaded MLX model: {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload MLX model {model_id}: {e}")
            return False