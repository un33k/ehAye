"""Base backend interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Iterator
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Information about a model."""
    id: str
    name: str
    size: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[str] = None
    family: Optional[str] = None
    format: Optional[str] = None
    installed: bool = False


@dataclass 
class ChatMessage:
    """Chat message structure."""
    role: str  # "user", "assistant", "system"
    content: str


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    temperature: float = 0.7
    max_tokens: int = 512
    top_p: float = 0.9
    stop_sequences: Optional[List[str]] = None
    stream: bool = False


class BaseBackend(ABC):
    """Abstract base class for LLM backends."""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available on the system."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[ModelInfo]:
        """List all installed models."""
        pass
    
    @abstractmethod
    def search_models(self, query: Optional[str] = None) -> List[ModelInfo]:
        """Search available models for download."""
        pass
    
    @abstractmethod
    def download_model(self, model_id: str, progress_callback: Optional[callable] = None) -> ModelInfo:
        """Download and install a model."""
        pass
    
    @abstractmethod
    def remove_model(self, model_id: str) -> bool:
        """Remove an installed model."""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Get detailed information about a model."""
        pass
    
    @abstractmethod
    def generate(
        self, 
        model_id: str, 
        messages: List[ChatMessage], 
        config: GenerationConfig
    ) -> Iterator[str]:
        """Generate text response from the model."""
        pass
    
    @abstractmethod
    def load_model(self, model_id: str) -> bool:
        """Load a model into memory for inference."""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        pass