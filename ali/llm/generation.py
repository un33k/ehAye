"""Text generation utilities."""

import time
from typing import Any, Dict, Generator, Optional, Tuple

from ..exceptions import ModelError
from ..logging import get_logger
from ..backends.manager import get_backend_manager

logger = get_logger("llm.generation")


class GenerationConfig:
    """Configuration for text generation."""
    
    def __init__(
        self,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        repetition_penalty: float = 1.1,
        seed: Optional[int] = None
    ):
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.seed = seed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MLX."""
        config = {
            "max_tokens": self.max_tokens,
            "temp": self.temperature,
        }
        
        if self.seed is not None:
            config["seed"] = self.seed
            
        return config
    
    def to_backend_config(self):
        """Convert to backend generation config."""
        from ..backends.base import GenerationConfig as BackendGenerationConfig
        return BackendGenerationConfig(
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )


class TextGenerator:
    """Handles text generation with backend models."""
    
    def __init__(self):
        self.backend_manager = get_backend_manager()
        self.current_model_id: Optional[str] = None
    
    def _get_backend_for_model(self, model_id: str):
        """Get the appropriate backend for a model."""
        # Try to find which backend has this model
        for backend_name in ["ollama", "mlx"]:
            try:
                backend = self.backend_manager.get_backend(backend_name)
                models = backend.list_models()
                if any(m.id == model_id for m in models):
                    return backend
            except Exception:
                continue
        
        # Default to primary backend
        return self.backend_manager.get_backend()
    
    def generate(
        self,
        prompt: str,
        model_id: str,
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate text response."""
        if not config:
            config = GenerationConfig()
        
        try:
            backend = self._get_backend_for_model(model_id)
            
            # Convert prompt to messages format for backend
            from ..backends.base import ChatMessage
            messages = [ChatMessage(role="user", content=prompt)]
            
            # Convert to backend config
            backend_config = config.to_backend_config()
            
            start_time = time.time()
            
            # Generate response (collect stream)
            response = ""
            for chunk in backend.generate(model_id, messages, backend_config):
                response += chunk
            
            generation_time = time.time() - start_time
            
            logger.debug(f"Generated {len(response)} chars in {generation_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise ModelError(f"Generation failed: {e}")
    
    def generate_stream(
        self,
        prompt: str,
        model_id: str,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """Generate text response with streaming."""
        if not config:
            config = GenerationConfig()
        
        try:
            backend = self._get_backend_for_model(model_id)
            
            # Convert prompt to messages format for backend
            from ..backends.base import ChatMessage
            messages = [ChatMessage(role="user", content=prompt)]
            
            # Convert to backend config
            backend_config = config.to_backend_config()
            
            # Stream response
            for chunk in backend.generate(model_id, messages, backend_config):
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise ModelError(f"Streaming generation failed: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimation: ~1.3 words per token for English
        words = len(text.split())
        return int(words * 1.3)
    
    def calculate_generation_stats(
        self, 
        response: str, 
        generation_time: float
    ) -> Dict[str, float]:
        """Calculate generation statistics."""
        char_count = len(response)
        word_count = len(response.split())
        token_estimate = self.estimate_tokens(response)
        
        chars_per_sec = char_count / generation_time if generation_time > 0 else 0
        words_per_sec = word_count / generation_time if generation_time > 0 else 0
        tokens_per_sec = token_estimate / generation_time if generation_time > 0 else 0
        
        return {
            "chars": char_count,
            "words": word_count,
            "tokens_estimated": token_estimate,
            "generation_time": generation_time,
            "chars_per_sec": chars_per_sec,
            "words_per_sec": words_per_sec,
            "tokens_per_sec": tokens_per_sec
        }


# Global generator instance
text_generator = TextGenerator()


def generate_text(
    prompt: str,
    model_id: str,
    config: Optional[GenerationConfig] = None
) -> str:
    """Generate text response."""
    return text_generator.generate(prompt, model_id, config)


def generate_text_stream(
    prompt: str,
    model_id: str,
    config: Optional[GenerationConfig] = None
) -> Generator[str, None, None]:
    """Generate text response with streaming."""
    return text_generator.generate_stream(prompt, model_id, config)


def create_generation_config(**kwargs) -> GenerationConfig:
    """Create a generation configuration."""
    return GenerationConfig(**kwargs)