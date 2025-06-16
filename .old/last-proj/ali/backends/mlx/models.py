"""MLX model management and registry."""

from typing import List, Dict, Optional, Set, Any
from pathlib import Path
from dataclasses import dataclass
import json

from ...exceptions import ModelNotFoundError, MLXModelFormatError, ModelValidationError
from ...logging import get_logger
from ...utilities import validate_path, get_file_size
from ..base import ModelInfo

logger = get_logger("backends.mlx.models")


@dataclass
class MLXModelSpec:
    """Specifications for an MLX model."""
    id: str
    name: str
    family: str
    size_params: str
    size_gb: Optional[float] = None
    description: Optional[str] = None
    source_repo: Optional[str] = None
    license: Optional[str] = None
    mlx_version: Optional[str] = None
    architecture: Optional[str] = None
    quantization: Optional[str] = None
    context_length: Optional[int] = None
    vocab_size: Optional[int] = None


class MLXModelManager:
    """Manages MLX model information and operations."""
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path.home() / ".cache" / "ehaye" / "models" / "mlx"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._model_registry = self._build_model_registry()
    
    def _build_model_registry(self) -> Dict[str, MLXModelSpec]:
        """Build registry of known MLX-compatible models."""
        models = [
            # Llama family
            MLXModelSpec(
                id="mlx-community/Llama-3.2-3B-Instruct-4bit",
                name="Llama 3.2 3B Instruct (4-bit)",
                family="llama",
                size_params="3B",
                size_gb=2.1,
                description="Llama 3.2 3B instruction-tuned, 4-bit quantized",
                source_repo="meta-llama/Llama-3.2-3B-Instruct",
                quantization="4bit",
                context_length=131072
            ),
            MLXModelSpec(
                id="mlx-community/Llama-3.2-1B-Instruct-4bit",
                name="Llama 3.2 1B Instruct (4-bit)",
                family="llama",
                size_params="1B",
                size_gb=0.9,
                description="Llama 3.2 1B instruction-tuned, 4-bit quantized",
                source_repo="meta-llama/Llama-3.2-1B-Instruct",
                quantization="4bit",
                context_length=131072
            ),
            MLXModelSpec(
                id="mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
                name="Llama 3.1 8B Instruct (4-bit)",
                family="llama",
                size_params="8B",
                size_gb=4.9,
                description="Llama 3.1 8B instruction-tuned, 4-bit quantized",
                source_repo="meta-llama/Meta-Llama-3.1-8B-Instruct",
                quantization="4bit",
                context_length=131072
            ),
            
            # Phi family
            MLXModelSpec(
                id="mlx-community/Phi-3.5-mini-instruct-4bit",
                name="Phi-3.5 Mini Instruct (4-bit)",
                family="phi",
                size_params="3.8B",
                size_gb=2.4,
                description="Microsoft Phi-3.5 Mini instruction-tuned, 4-bit quantized",
                source_repo="microsoft/Phi-3.5-mini-instruct",
                quantization="4bit",
                context_length=131072
            ),
            MLXModelSpec(
                id="mlx-community/Phi-3-mini-4k-instruct-4bit",
                name="Phi-3 Mini 4K Instruct (4-bit)",
                family="phi",
                size_params="3.8B",
                size_gb=2.4,
                description="Microsoft Phi-3 Mini 4K instruction-tuned, 4-bit quantized",
                source_repo="microsoft/Phi-3-mini-4k-instruct",
                quantization="4bit",
                context_length=4096
            ),
            
            # Gemma family
            MLXModelSpec(
                id="mlx-community/gemma-2-2b-it-4bit",
                name="Gemma 2 2B IT (4-bit)",
                family="gemma",
                size_params="2B",
                size_gb=1.7,
                description="Google Gemma 2 2B instruction-tuned, 4-bit quantized",
                source_repo="google/gemma-2-2b-it",
                quantization="4bit",
                context_length=8192
            ),
            MLXModelSpec(
                id="mlx-community/gemma-2-9b-it-4bit",
                name="Gemma 2 9B IT (4-bit)",
                family="gemma",
                size_params="9B",
                size_gb=5.4,
                description="Google Gemma 2 9B instruction-tuned, 4-bit quantized",
                source_repo="google/gemma-2-9b-it",
                quantization="4bit",
                context_length=8192
            ),
            
            # Qwen family
            MLXModelSpec(
                id="mlx-community/Qwen2.5-1.5B-Instruct-4bit",
                name="Qwen 2.5 1.5B Instruct (4-bit)",
                family="qwen",
                size_params="1.5B",
                size_gb=1.1,
                description="Alibaba Qwen 2.5 1.5B instruction-tuned, 4-bit quantized",
                source_repo="Qwen/Qwen2.5-1.5B-Instruct",
                quantization="4bit",
                context_length=32768
            ),
            MLXModelSpec(
                id="mlx-community/Qwen2.5-7B-Instruct-4bit",
                name="Qwen 2.5 7B Instruct (4-bit)",
                family="qwen",
                size_params="7B",
                size_gb=4.3,
                description="Alibaba Qwen 2.5 7B instruction-tuned, 4-bit quantized",
                source_repo="Qwen/Qwen2.5-7B-Instruct",
                quantization="4bit",
                context_length=32768
            ),
            
            # Mistral family
            MLXModelSpec(
                id="mlx-community/Mistral-7B-Instruct-v0.3-4bit",
                name="Mistral 7B Instruct v0.3 (4-bit)",
                family="mistral",
                size_params="7B",
                size_gb=4.1,
                description="Mistral 7B v0.3 instruction-tuned, 4-bit quantized",
                source_repo="mistralai/Mistral-7B-Instruct-v0.3",
                quantization="4bit",
                context_length=32768
            ),
            
            # Code models
            MLXModelSpec(
                id="mlx-community/CodeLlama-7b-Instruct-hf-4bit",
                name="Code Llama 7B Instruct (4-bit)",
                family="llama",
                size_params="7B",
                size_gb=3.9,
                description="Meta Code Llama 7B instruction-tuned, 4-bit quantized",
                source_repo="codellama/CodeLlama-7b-Instruct-hf",
                quantization="4bit",
                context_length=16384
            ),
            MLXModelSpec(
                id="mlx-community/CodeQwen1.5-7B-Chat-4bit",
                name="CodeQwen 1.5 7B Chat (4-bit)",
                family="qwen",
                size_params="7B",
                size_gb=4.2,
                description="Alibaba CodeQwen 1.5 7B chat model, 4-bit quantized",
                source_repo="Qwen/CodeQwen1.5-7B-Chat",
                quantization="4bit",
                context_length=65536
            ),
            
            # Small/efficient models
            MLXModelSpec(
                id="mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit",
                name="TinyLlama 1.1B Chat (4-bit)",
                family="llama",
                size_params="1.1B",
                size_gb=0.8,
                description="TinyLlama 1.1B chat model, 4-bit quantized",
                source_repo="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                quantization="4bit",
                context_length=2048
            ),
        ]
        
        return {model.id: model for model in models}
    
    def get_model_spec(self, model_id: str) -> Optional[MLXModelSpec]:
        """Get model specification by ID."""
        return self._model_registry.get(model_id)
    
    def search_models(self, query: str) -> List[MLXModelSpec]:
        """Search models by query."""
        query_lower = query.lower()
        results = []
        
        for model in self._model_registry.values():
            if (query_lower in model.id.lower() or
                query_lower in model.name.lower() or
                query_lower in model.family.lower() or
                (model.description and query_lower in model.description.lower())):
                results.append(model)
        
        return results
    
    def get_models_by_family(self, family: str) -> List[MLXModelSpec]:
        """Get all models from a specific family."""
        return [model for model in self._model_registry.values() if model.family == family]
    
    def get_models_by_size(self, max_size_gb: float) -> List[MLXModelSpec]:
        """Get models within a size limit."""
        results = []
        for model in self._model_registry.values():
            if model.size_gb and model.size_gb <= max_size_gb:
                results.append(model)
        return results
    
    def categorize_by_size(self) -> Dict[str, List[MLXModelSpec]]:
        """Categorize models by parameter size."""
        categories = {
            "tiny": [],      # < 2B
            "small": [],     # 2B - 3B
            "medium": [],    # 3B - 8B
            "large": [],     # > 8B
        }
        
        for model in self._model_registry.values():
            size_num = self._extract_param_size(model.size_params)
            
            if size_num < 2.0:
                categories["tiny"].append(model)
            elif size_num < 3.0:
                categories["small"].append(model)
            elif size_num < 8.0:
                categories["medium"].append(model)
            else:
                categories["large"].append(model)
        
        return categories
    
    def get_recommended_models(self, use_case: str = "general") -> List[MLXModelSpec]:
        """Get recommended models for a specific use case."""
        recommendations = {
            "general": ["mlx-community/Llama-3.2-3B-Instruct-4bit", "mlx-community/Phi-3.5-mini-instruct-4bit"],
            "coding": ["mlx-community/CodeLlama-7b-Instruct-hf-4bit", "mlx-community/CodeQwen1.5-7B-Chat-4bit"],
            "chat": ["mlx-community/Llama-3.2-1B-Instruct-4bit", "mlx-community/gemma-2-2b-it-4bit"],
            "fast": ["mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit", "mlx-community/Qwen2.5-1.5B-Instruct-4bit"],
            "quality": ["mlx-community/Meta-Llama-3.1-8B-Instruct-4bit", "mlx-community/Qwen2.5-7B-Instruct-4bit"],
        }
        
        model_ids = recommendations.get(use_case, recommendations["general"])
        return [self._model_registry[mid] for mid in model_ids if mid in self._model_registry]
    
    def validate_model_directory(self, model_path: Path) -> Dict[str, Any]:
        """Validate MLX model directory structure."""
        validation = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "files_found": [],
            "missing_files": [],
        }
        
        required_files = ["config.json", "model.safetensors"]
        optional_files = ["tokenizer.model", "tokenizer.json", "special_tokens_map.json", "tokenizer_config.json"]
        
        if not model_path.exists():
            validation["errors"].append(f"Model directory does not exist: {model_path}")
            return validation
        
        if not model_path.is_dir():
            validation["errors"].append(f"Model path is not a directory: {model_path}")
            return validation
        
        # Check for required files
        for file_name in required_files:
            file_path = model_path / file_name
            if file_path.exists():
                validation["files_found"].append(file_name)
            else:
                validation["missing_files"].append(file_name)
                validation["errors"].append(f"Required file missing: {file_name}")
        
        # Check for optional files
        for file_name in optional_files:
            file_path = model_path / file_name
            if file_path.exists():
                validation["files_found"].append(file_name)
        
        # Validate config.json
        config_path = model_path / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check for required config fields
                required_config_fields = ["model_type", "vocab_size"]
                for field in required_config_fields:
                    if field not in config:
                        validation["warnings"].append(f"Config missing recommended field: {field}")
                
            except json.JSONDecodeError as e:
                validation["errors"].append(f"Invalid JSON in config.json: {e}")
            except Exception as e:
                validation["errors"].append(f"Error reading config.json: {e}")
        
        # Check model file size
        model_file = model_path / "model.safetensors"
        if model_file.exists():
            try:
                size_mb = get_file_size(model_file) / (1024 * 1024)
                if size_mb < 10:  # Very small model file might be corrupt
                    validation["warnings"].append(f"Model file unusually small: {size_mb:.1f}MB")
            except Exception as e:
                validation["warnings"].append(f"Could not check model file size: {e}")
        
        validation["valid"] = len(validation["errors"]) == 0
        return validation
    
    def get_installed_models(self) -> List[MLXModelSpec]:
        """Get list of locally installed MLX models."""
        installed = []
        
        if not self.models_dir.exists():
            return installed
        
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                # Check if it's a valid MLX model
                validation = self.validate_model_directory(model_dir)
                
                if validation["valid"]:
                    # Try to find matching spec in registry
                    model_id = model_dir.name
                    spec = self.get_model_spec(model_id)
                    
                    if spec:
                        installed.append(spec)
                    else:
                        # Create spec from local model
                        try:
                            config_path = model_dir / "config.json"
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                            
                            installed.append(MLXModelSpec(
                                id=model_id,
                                name=model_id,
                                family=config.get("model_type", "unknown"),
                                size_params="unknown",
                                description="Local MLX model",
                                architecture=config.get("architectures", [None])[0]
                            ))
                        except Exception as e:
                            logger.warning(f"Could not create spec for local model {model_id}: {e}")
        
        return installed
    
    def estimate_memory_usage(self, model_id: str, precision: str = "4bit") -> Optional[float]:
        """Estimate memory usage for an MLX model."""
        spec = self.get_model_spec(model_id)
        if not spec:
            return None
        
        # For MLX models, use the quantized size as a good estimate
        if spec.size_gb:
            # Add some overhead for model execution
            return spec.size_gb * 1.3
        
        # Fallback calculation based on parameters
        param_size = self._extract_param_size(spec.size_params)
        
        # MLX 4-bit quantization is quite efficient
        memory_multipliers = {
            "4bit": 0.6,   # 4-bit quantization with overhead
            "8bit": 1.1,   # 8-bit quantization with overhead
            "fp16": 2.2,   # Half precision with overhead
            "fp32": 4.4,   # Full precision with overhead
        }
        
        multiplier = memory_multipliers.get(precision, 0.6)
        return param_size * multiplier
    
    def _extract_param_size(self, size_str: str) -> float:
        """Extract numeric parameter size from string."""
        if not size_str:
            return 0.0
        
        import re
        match = re.match(r'(\d+(?:\.\d+)?)\s*([KMGT]?B?)', size_str.upper())
        if not match:
            return 0.0
        
        number, unit = match.groups()
        number = float(number)
        
        unit_multipliers = {
            'M': 0.001,
            'MB': 0.001,
            'B': 1.0,
            'GB': 1000.0,
            'T': 1000000.0,
            'TB': 1000000.0,
            '': 1.0,
        }
        
        multiplier = unit_multipliers.get(unit, 1.0)
        return number * multiplier
    
    def to_model_info(self, spec: MLXModelSpec, installed: bool = False) -> ModelInfo:
        """Convert MLXModelSpec to ModelInfo."""
        return ModelInfo(
            id=spec.id,
            name=spec.name,
            size=spec.size_params,
            description=spec.description,
            parameters=spec.size_params,
            family=spec.family,
            format="mlx",
            installed=installed
        )