"""Ollama model management utilities."""

import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

from ...exceptions import ModelNotFoundError, ModelDownloadError
from ...logging import get_logger
from ..base import ModelInfo

logger = get_logger("backends.ollama.models")


@dataclass
class OllamaModelSpec:
    """Specifications for an Ollama model."""
    id: str
    name: str
    family: str
    size_params: str
    size_gb: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    license: Optional[str] = None
    capabilities: Optional[List[str]] = None


class OllamaModelManager:
    """Manages Ollama model information and operations."""
    
    def __init__(self):
        self._model_registry = self._build_model_registry()
    
    def _build_model_registry(self) -> Dict[str, OllamaModelSpec]:
        """Build registry of known Ollama models."""
        models = [
            # Llama family
            OllamaModelSpec(
                id="llama3.2",
                name="Llama 3.2",
                family="llama",
                size_params="3B",
                size_gb=2.0,
                description="Meta's Llama 3.2 model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="llama3.2:1b",
                name="Llama 3.2 1B",
                family="llama",
                size_params="1B",
                size_gb=1.3,
                description="Smaller Llama 3.2 model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="llama3.1",
                name="Llama 3.1",
                family="llama",
                size_params="8B",
                size_gb=4.7,
                description="Meta's Llama 3.1 model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="llama3.1:70b",
                name="Llama 3.1 70B",
                family="llama",
                size_params="70B",
                size_gb=40.0,
                description="Large Llama 3.1 model",
                capabilities=["text-generation", "chat"]
            ),
            
            # Phi family
            OllamaModelSpec(
                id="phi3",
                name="Phi-3",
                family="phi",
                size_params="3.8B",
                size_gb=2.3,
                description="Microsoft's Phi-3 model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="phi3:mini",
                name="Phi-3 Mini",
                family="phi",
                size_params="3.8B",
                size_gb=2.3,
                description="Compact Phi-3 model",
                capabilities=["text-generation", "chat"]
            ),
            
            # Gemma family
            OllamaModelSpec(
                id="gemma2",
                name="Gemma 2",
                family="gemma",
                size_params="9B",
                size_gb=5.4,
                description="Google's Gemma 2 model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="gemma2:2b",
                name="Gemma 2 2B",
                family="gemma",
                size_params="2B",
                size_gb=1.6,
                description="Smaller Gemma 2 model",
                capabilities=["text-generation", "chat"]
            ),
            
            # Qwen family
            OllamaModelSpec(
                id="qwen2",
                name="Qwen 2",
                family="qwen",
                size_params="7B",
                size_gb=4.4,
                description="Alibaba's Qwen 2 model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="qwen2:1.5b",
                name="Qwen 2 1.5B",
                family="qwen",
                size_params="1.5B",
                size_gb=1.0,
                description="Compact Qwen 2 model",
                capabilities=["text-generation", "chat"]
            ),
            
            # Mistral family
            OllamaModelSpec(
                id="mistral",
                name="Mistral 7B",
                family="mistral",
                size_params="7B",
                size_gb=4.1,
                description="Mistral AI's 7B model",
                capabilities=["text-generation", "chat"]
            ),
            OllamaModelSpec(
                id="mixtral",
                name="Mixtral 8x7B",
                family="mistral",
                size_params="47B",
                size_gb=26.0,
                description="Mistral AI's mixture of experts model",
                capabilities=["text-generation", "chat"]
            ),
            
            # Code models
            OllamaModelSpec(
                id="codellama",
                name="Code Llama",
                family="llama",
                size_params="7B",
                size_gb=3.8,
                description="Meta's Code Llama model",
                capabilities=["code-generation", "text-generation"]
            ),
            OllamaModelSpec(
                id="codellama:7b-python",
                name="Code Llama Python",
                family="llama",
                size_params="7B",
                size_gb=3.8,
                description="Code Llama specialized for Python",
                capabilities=["code-generation", "python"]
            ),
            OllamaModelSpec(
                id="deepseek-coder",
                name="DeepSeek Coder",
                family="deepseek",
                size_params="6.7B",
                size_gb=3.8,
                description="DeepSeek's coding model",
                capabilities=["code-generation", "text-generation"]
            ),
            
            # Embedding models
            OllamaModelSpec(
                id="nomic-embed-text",
                name="Nomic Embed Text",
                family="nomic",
                size_params="137M",
                size_gb=0.3,
                description="Text embedding model",
                capabilities=["embedding"]
            ),
            OllamaModelSpec(
                id="all-minilm",
                name="All-MiniLM",
                family="sentence-transformers",
                size_params="22M",
                size_gb=0.1,
                description="Sentence embedding model",
                capabilities=["embedding"]
            ),
        ]
        
        return {model.id: model for model in models}
    
    def get_model_spec(self, model_id: str) -> Optional[OllamaModelSpec]:
        """Get model specification by ID."""
        return self._model_registry.get(model_id)
    
    def search_models(self, query: str) -> List[OllamaModelSpec]:
        """Search models by query."""
        query_lower = query.lower()
        results = []
        
        for model in self._model_registry.values():
            # Search in ID, name, family, and description
            if (query_lower in model.id.lower() or
                query_lower in model.name.lower() or
                query_lower in model.family.lower() or
                (model.description and query_lower in model.description.lower())):
                results.append(model)
        
        return results
    
    def get_models_by_family(self, family: str) -> List[OllamaModelSpec]:
        """Get all models from a specific family."""
        return [model for model in self._model_registry.values() if model.family == family]
    
    def get_models_by_capability(self, capability: str) -> List[OllamaModelSpec]:
        """Get models with a specific capability."""
        results = []
        for model in self._model_registry.values():
            if model.capabilities and capability in model.capabilities:
                results.append(model)
        return results
    
    def categorize_by_size(self) -> Dict[str, List[OllamaModelSpec]]:
        """Categorize models by parameter size."""
        categories = {
            "tiny": [],      # < 2B
            "small": [],     # 2B - 3B
            "medium": [],    # 3B - 8B
            "large": [],     # 8B - 20B
            "xl": [],        # > 20B
        }
        
        for model in self._model_registry.values():
            size_num = self._extract_param_size(model.size_params)
            
            if size_num < 2.0:
                categories["tiny"].append(model)
            elif size_num < 3.0:
                categories["small"].append(model)
            elif size_num < 8.0:
                categories["medium"].append(model)
            elif size_num < 20.0:
                categories["large"].append(model)
            else:
                categories["xl"].append(model)
        
        return categories
    
    def get_recommended_models(self, use_case: str = "general") -> List[OllamaModelSpec]:
        """Get recommended models for a specific use case."""
        recommendations = {
            "general": ["llama3.2", "phi3", "gemma2:2b"],
            "coding": ["codellama", "deepseek-coder", "codellama:7b-python"],
            "chat": ["llama3.2", "phi3:mini", "qwen2:1.5b"],
            "embedding": ["nomic-embed-text", "all-minilm"],
            "fast": ["phi3:mini", "gemma2:2b", "qwen2:1.5b"],
            "quality": ["llama3.1", "mistral", "gemma2"],
        }
        
        model_ids = recommendations.get(use_case, recommendations["general"])
        return [self._model_registry[mid] for mid in model_ids if mid in self._model_registry]
    
    def validate_model_id(self, model_id: str) -> bool:
        """Validate if a model ID is properly formatted."""
        # Ollama model ID pattern: name[:tag]
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*(?::[a-zA-Z0-9][a-zA-Z0-9._-]*)?$'
        return bool(re.match(pattern, model_id))
    
    def parse_model_id(self, model_id: str) -> Dict[str, str]:
        """Parse model ID into components."""
        if ':' in model_id:
            name, tag = model_id.split(':', 1)
        else:
            name, tag = model_id, 'latest'
        
        return {
            "full_id": model_id,
            "name": name,
            "tag": tag,
        }
    
    def estimate_memory_usage(self, model_id: str, precision: str = "fp16") -> Optional[float]:
        """Estimate memory usage for a model."""
        spec = self.get_model_spec(model_id)
        if not spec:
            return None
        
        # Rough estimation based on parameters and precision
        param_size = self._extract_param_size(spec.size_params)
        
        # Memory multipliers for different precisions
        multipliers = {
            "fp32": 4.0,  # 4 bytes per parameter
            "fp16": 2.0,  # 2 bytes per parameter
            "int8": 1.0,  # 1 byte per parameter
            "int4": 0.5,  # 0.5 bytes per parameter
        }
        
        multiplier = multipliers.get(precision, 2.0)
        memory_gb = param_size * multiplier
        
        # Add overhead (roughly 20%)
        return memory_gb * 1.2
    
    def _extract_param_size(self, size_str: str) -> float:
        """Extract numeric parameter size from string."""
        if not size_str:
            return 0.0
        
        # Extract number and unit
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B?)', size_str.upper())
        if not match:
            return 0.0
        
        number, unit = match.groups()
        number = float(number)
        
        # Convert to billions
        unit_multipliers = {
            'M': 0.001,     # Million to billion
            'MB': 0.001,
            'B': 1.0,       # Already in billions
            'G': 1000.0,    # Billion parameters (GB would be bytes)
            'GB': 1000.0,
            'T': 1000000.0, # Trillion to billion
            'TB': 1000000.0,
            '': 1.0,        # Assume billions if no unit
        }
        
        multiplier = unit_multipliers.get(unit, 1.0)
        return number * multiplier
    
    def to_model_info(self, spec: OllamaModelSpec, installed: bool = False) -> ModelInfo:
        """Convert OllamaModelSpec to ModelInfo."""
        return ModelInfo(
            id=spec.id,
            name=spec.name,
            size=spec.size_params,
            description=spec.description,
            parameters=spec.size_params,
            family=spec.family,
            format="ollama",
            installed=installed
        )