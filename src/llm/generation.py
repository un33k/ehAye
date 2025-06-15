"""Text generation utilities."""

import time
from typing import Any, Dict, Generator, Optional, Tuple

from ..core.exceptions import ModelError
from ..core.logging import get_logger
from ..models.loader import get_loaded_model, is_model_loaded, load_model

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


class TextGenerator:
    """Handles text generation with MLX models."""
    
    def __init__(self):
        self.current_model_id: Optional[str] = None
    
    def ensure_model_loaded(self, model_id: str) -> Tuple[Any, Any]:
        """Ensure the specified model is loaded."""
        if not is_model_loaded(model_id):
            logger.info(f"Loading model for generation: {model_id}")
            return load_model(model_id)
        
        loaded = get_loaded_model()
        if loaded:
            return loaded[1], loaded[2]  # model, tokenizer
        
        raise ModelError("No model loaded")
    
    def generate(
        self,
        prompt: str,
        model_id: str,
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate text response."""
        if not config:
            config = GenerationConfig()
        
        model, tokenizer = self.ensure_model_loaded(model_id)
        
        try:
            from mlx_lm import generate
            from mlx_lm.sample_utils import make_sampler
            
            # Create sampler
            sampler = make_sampler(
                temp=config.temperature,
                top_p=config.top_p if hasattr(config, 'top_p') else None
            )
            
            start_time = time.time()
            
            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=config.max_tokens,
                sampler=sampler,
                verbose=False
            )
            
            generation_time = time.time() - start_time
            
            # Clean up response
            if prompt in response:
                response = response.replace(prompt, "").strip()
            
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
        
        model, tokenizer = self.ensure_model_loaded(model_id)
        
        try:
            from mlx_lm.generate import stream_generate
            from mlx_lm.sample_utils import make_sampler
            
            # Create sampler
            sampler = make_sampler(
                temp=config.temperature,
                top_p=config.top_p if hasattr(config, 'top_p') else None
            )
            
            for chunk in stream_generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=config.max_tokens,
                sampler=sampler
            ):
                yield chunk.text
                
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