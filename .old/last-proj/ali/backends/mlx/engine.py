"""MLX inference engine for Apple Silicon optimization."""

from typing import List, Dict, Optional, Iterator, Any, Tuple
from pathlib import Path
import json

from ...exceptions import MLXError, MLXNotAvailableError, MLXMemoryError, ModelLoadError
from ...logging import get_logger
from ...utilities import check_apple_silicon
from ..base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig

logger = get_logger("backends.mlx.engine")


class MLXEngine(BaseBackend):
    """MLX-optimized inference engine for Apple Silicon."""
    
    def __init__(self):
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        self._check_mlx_availability()
    
    def _check_mlx_availability(self) -> None:
        """Check if MLX is available and properly configured."""
        if not check_apple_silicon():
            raise MLXNotAvailableError("darwin", "arm64")
        
        try:
            import mlx.core as mx
            import mlx.nn as nn
            self.mx = mx
            self.nn = nn
        except ImportError as e:
            raise MLXError("MLX not installed", cause=e)
    
    def is_available(self) -> bool:
        """Check if MLX backend is available."""
        try:
            self._check_mlx_availability()
            return True
        except (MLXError, MLXNotAvailableError):
            return False
    
    def list_models(self) -> List[ModelInfo]:
        """List installed MLX models."""
        try:
            from ...models.registry import get_installed_models
            models = get_installed_models(backend="mlx")
            
            return [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    size=model.size_params,
                    description=f"MLX {model.category} model",
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
        """Search available MLX models."""
        try:
            from ...models.registry import search_models
            models = search_models(query=query, backend="mlx")
            
            return [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    size=model.size_params,
                    description=f"MLX {model.category} model",
                    family=model.category,
                    format="mlx",
                    installed=False
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Failed to search MLX models: {e}")
            return []
    
    def download_model(self, model_id: str, progress_callback: Optional[callable] = None) -> ModelInfo:
        """Download and convert model to MLX format."""
        try:
            from ...models.manager import download_model
            model_info = download_model(model_id, backend="mlx", progress_callback=progress_callback)
            
            return ModelInfo(
                id=model_info.id,
                name=model_info.name,
                size=model_info.size_params,
                description=f"MLX {model_info.category} model",
                family=model_info.category,
                format="mlx",
                installed=True
            )
        except Exception as e:
            logger.error(f"Failed to download MLX model {model_id}: {e}")
            raise
    
    def remove_model(self, model_id: str) -> bool:
        """Remove an MLX model."""
        try:
            from ...models.manager import remove_model
            return remove_model(model_id, backend="mlx")
        except Exception as e:
            logger.error(f"Failed to remove MLX model {model_id}: {e}")
            return False
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed information about an MLX model."""
        try:
            from ...models.registry import get_model_info
            model = get_model_info(model_id, backend="mlx")
            
            if model:
                return ModelInfo(
                    id=model.id,
                    name=model.name,
                    size=model.size_params,
                    description=f"MLX {model.category} model - {model.size_gb:.1f}GB" if model.size_gb else f"MLX {model.category} model",
                    parameters=model.size_params,
                    family=model.category,
                    format="mlx",
                    installed=True
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get MLX model info for {model_id}: {e}")
            return None
    
    def load_model(self, model_id: str) -> bool:
        """Load MLX model into memory."""
        if model_id in self.loaded_models:
            logger.debug(f"Model {model_id} already loaded")
            return True
        
        try:
            model, tokenizer = self._load_mlx_model(model_id)
            
            self.loaded_models[model_id] = {
                'model': model,
                'tokenizer': tokenizer,
                'config': self._get_model_config(model_id)
            }
            
            logger.info(f"Successfully loaded MLX model: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load MLX model {model_id}: {e}")
            return False
    
    def unload_model(self, model_id: str) -> bool:
        """Unload MLX model from memory."""
        try:
            if model_id in self.loaded_models:
                del self.loaded_models[model_id]
                
                # Trigger garbage collection for MLX arrays
                import gc
                gc.collect()
                
                logger.info(f"Unloaded MLX model: {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload MLX model {model_id}: {e}")
            return False
    
    def generate(
        self,
        model_id: str,
        messages: List[ChatMessage],
        config: GenerationConfig
    ) -> Iterator[str]:
        """Generate text using MLX model."""
        try:
            # Ensure model is loaded
            if not self.load_model(model_id):
                yield f"Error: Failed to load model {model_id}"
                return
            
            model_data = self.loaded_models[model_id]
            model = model_data['model']
            tokenizer = model_data['tokenizer']
            
            # Format messages into prompt
            prompt = self._format_messages_for_model(messages, model_id)
            
            # Tokenize input
            tokens = tokenizer.encode(prompt)
            
            if config.stream:
                # Streaming generation
                yield from self._generate_streaming(
                    model, tokenizer, tokens, config
                )
            else:
                # Non-streaming generation
                response = self._generate_complete(
                    model, tokenizer, tokens, config
                )
                yield response
                
        except Exception as e:
            logger.error(f"Error generating text with MLX: {e}")
            yield f"Error: {e}"
    
    def _load_mlx_model(self, model_id: str) -> Tuple[Any, Any]:
        """Load MLX model and tokenizer."""
        try:
            from ...models.loader import load_model
            return load_model(model_id, backend="mlx")
        except Exception as e:
            raise ModelLoadError(model_id, f"MLX model loading failed: {e}", cause=e)
    
    def _get_model_config(self, model_id: str) -> Dict[str, Any]:
        """Get model configuration."""
        try:
            from ...models.registry import get_model_config
            return get_model_config(model_id, backend="mlx")
        except Exception:
            return {}
    
    def _format_messages_for_model(self, messages: List[ChatMessage], model_id: str) -> str:
        """Format messages for the specific model."""
        try:
            from ...llm.prompts import format_messages
            return format_messages(messages, model_id)
        except ImportError:
            # Fallback formatting
            return self._simple_format_messages(messages)
    
    def _simple_format_messages(self, messages: List[ChatMessage]) -> str:
        """Simple message formatting fallback."""
        if len(messages) == 1:
            return messages[0].content
        
        formatted = []
        for msg in messages:
            if msg.role == "user":
                formatted.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Assistant: {msg.content}")
            elif msg.role == "system":
                formatted.append(f"System: {msg.content}")
        
        return "\n".join(formatted) + "\nAssistant:"
    
    def _generate_streaming(
        self,
        model: Any,
        tokenizer: Any,
        input_tokens: List[int],
        config: GenerationConfig
    ) -> Iterator[str]:
        """Generate text with streaming output."""
        try:
            import mlx.core as mx
            
            # Convert to MLX array
            tokens = mx.array(input_tokens)[None]  # Add batch dimension
            
            generated_tokens = []
            max_new_tokens = config.max_tokens
            
            for i in range(max_new_tokens):
                # Get logits from model
                logits = model(tokens)
                
                # Apply temperature
                if config.temperature != 1.0:
                    logits = logits / config.temperature
                
                # Apply top-p filtering if specified
                if config.top_p < 1.0:
                    logits = self._apply_top_p(logits, config.top_p)
                
                # Sample next token
                probs = mx.softmax(logits[:, -1, :], axis=-1)
                next_token = mx.random.categorical(probs)
                
                # Convert to Python int
                next_token_id = int(next_token.item())
                
                # Check for stop sequences
                if self._should_stop(next_token_id, tokenizer, config.stop_sequences):
                    break
                
                # Decode and yield token
                token_text = tokenizer.decode([next_token_id])
                yield token_text
                
                # Update tokens for next iteration
                tokens = mx.concatenate([tokens, next_token[None, None]], axis=1)
                generated_tokens.append(next_token_id)
            
        except Exception as e:
            logger.error(f"Streaming generation error: {e}")
            yield f"Error: {e}"
    
    def _generate_complete(
        self,
        model: Any,
        tokenizer: Any,
        input_tokens: List[int],
        config: GenerationConfig
    ) -> str:
        """Generate complete text response."""
        try:
            import mlx.core as mx
            
            tokens = mx.array(input_tokens)[None]
            generated_tokens = []
            max_new_tokens = config.max_tokens
            
            for i in range(max_new_tokens):
                logits = model(tokens)
                
                if config.temperature != 1.0:
                    logits = logits / config.temperature
                
                if config.top_p < 1.0:
                    logits = self._apply_top_p(logits, config.top_p)
                
                probs = mx.softmax(logits[:, -1, :], axis=-1)
                next_token = mx.random.categorical(probs)
                next_token_id = int(next_token.item())
                
                if self._should_stop(next_token_id, tokenizer, config.stop_sequences):
                    break
                
                tokens = mx.concatenate([tokens, next_token[None, None]], axis=1)
                generated_tokens.append(next_token_id)
            
            # Decode all generated tokens
            return tokenizer.decode(generated_tokens)
            
        except Exception as e:
            logger.error(f"Complete generation error: {e}")
            return f"Error: {e}"
    
    def _apply_top_p(self, logits: Any, top_p: float) -> Any:
        """Apply top-p (nucleus) sampling."""
        import mlx.core as mx
        
        # Sort logits in descending order
        sorted_logits, sorted_indices = mx.sort(logits, axis=-1)[::-1]
        
        # Calculate cumulative probabilities
        probs = mx.softmax(sorted_logits, axis=-1)
        cumulative_probs = mx.cumsum(probs, axis=-1)
        
        # Create mask for tokens to keep
        keep_mask = cumulative_probs <= top_p
        
        # Always keep at least one token (the highest probability)
        keep_mask = mx.concatenate([mx.ones_like(keep_mask[..., :1]), keep_mask[..., 1:]], axis=-1)
        
        # Set logits of filtered tokens to negative infinity
        filtered_logits = mx.where(keep_mask, sorted_logits, -mx.inf)
        
        # Unsort to original order
        original_logits = mx.zeros_like(logits)
        original_logits = mx.scatter(original_logits, sorted_indices, filtered_logits, axis=-1)
        
        return original_logits
    
    def _should_stop(
        self,
        token_id: int,
        tokenizer: Any,
        stop_sequences: Optional[List[str]]
    ) -> bool:
        """Check if generation should stop."""
        if not stop_sequences:
            return False
        
        token_text = tokenizer.decode([token_id])
        
        for stop_seq in stop_sequences:
            if stop_seq in token_text:
                return True
        
        return False
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            import mlx.core as mx
            
            # Get MLX memory info
            memory_info = {
                "device": "Apple Silicon GPU",
                "loaded_models": len(self.loaded_models),
                "model_names": list(self.loaded_models.keys()),
            }
            
            # Try to get MLX-specific memory info if available
            try:
                # This might not be available in all MLX versions
                memory_info["mlx_memory_mb"] = mx.metal.get_memory_info()
            except:
                pass
            
            return memory_info
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {"error": str(e)}