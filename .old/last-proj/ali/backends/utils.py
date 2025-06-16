"""Backend utilities and helper functions."""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json

from ..exceptions import BackendError, ModelNotFoundError
from ..logging import get_logger
from ..utilities import validate_model_name, get_system_info
from .base import ModelInfo, BaseBackend

logger = get_logger("backends.utils")


def detect_available_backends() -> List[str]:
    """Detect which backends are available on the system."""
    available = []
    
    # Check Ollama
    try:
        import subprocess
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            available.append("ollama")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    # Check MLX
    try:
        import mlx.core as mx
        from ..utilities import check_apple_silicon
        if check_apple_silicon():
            available.append("mlx")
    except ImportError:
        pass
    
    return available


def compare_model_info(model1: ModelInfo, model2: ModelInfo) -> Dict[str, Any]:
    """Compare two models and return differences."""
    comparison = {
        "same_id": model1.id == model2.id,
        "same_name": model1.name == model2.name,
        "same_family": model1.family == model2.family,
        "same_format": model1.format == model2.format,
        "differences": [],
    }
    
    # Check specific differences
    if model1.size != model2.size:
        comparison["differences"].append(f"Size: {model1.size} vs {model2.size}")
    
    if model1.description != model2.description:
        comparison["differences"].append(f"Description differs")
    
    if model1.parameters != model2.parameters:
        comparison["differences"].append(f"Parameters: {model1.parameters} vs {model2.parameters}")
    
    if model1.installed != model2.installed:
        comparison["differences"].append(f"Installation: {model1.installed} vs {model2.installed}")
    
    return comparison


def standardize_model_id(model_id: str, backend: str) -> str:
    """Standardize model ID format for different backends."""
    validate_model_name(model_id)
    
    if backend == "ollama":
        # Ollama uses simple names, optionally with tags
        return model_id.lower()
    
    elif backend == "mlx":
        # MLX often uses HuggingFace-style paths
        if not model_id.startswith("mlx-community/"):
            # Add prefix if missing
            if "/" not in model_id:
                model_id = f"mlx-community/{model_id}"
        return model_id
    
    return model_id


def extract_model_family(model_id: str) -> str:
    """Extract model family from model ID."""
    model_id_lower = model_id.lower()
    
    # Common model families
    families = {
        "llama": ["llama", "alpaca", "vicuna"],
        "phi": ["phi"],
        "gemma": ["gemma"],
        "qwen": ["qwen", "codeqwen"],
        "mistral": ["mistral", "mixtral"],
        "codellama": ["codellama", "code-llama"],
        "deepseek": ["deepseek"],
        "nomic": ["nomic"],
        "bert": ["bert"],
        "gpt": ["gpt"],
        "claude": ["claude"],
    }
    
    for family, keywords in families.items():
        for keyword in keywords:
            if keyword in model_id_lower:
                return family
    
    return "unknown"


def estimate_download_time(size_gb: float, bandwidth_mbps: float = 100) -> float:
    """Estimate download time in seconds."""
    if bandwidth_mbps <= 0:
        return float('inf')
    
    # Convert GB to Mb and calculate time
    size_mb = size_gb * 8 * 1024  # GB to megabits
    time_seconds = size_mb / bandwidth_mbps
    
    return time_seconds


def format_model_size(size_str: Optional[str]) -> Optional[str]:
    """Format model size string consistently."""
    if not size_str:
        return None
    
    # Normalize common variations
    size_str = size_str.upper().strip()
    
    # Replace common variations
    replacements = {
        "BILLION": "B",
        "MILLION": "M", 
        "PARAMETERS": "",
        "PARAMS": "",
        " ": "",
    }
    
    for old, new in replacements.items():
        size_str = size_str.replace(old, new)
    
    return size_str


def get_recommended_backend(model_id: str, system_info: Optional[Dict] = None) -> str:
    """Get recommended backend for a model."""
    if system_info is None:
        system_info = get_system_info()
    
    model_family = extract_model_family(model_id)
    is_apple_silicon = system_info.get('architecture') == 'arm64' and system_info.get('platform') == 'Darwin'
    
    # For Apple Silicon, prefer MLX when available
    if is_apple_silicon:
        available_backends = detect_available_backends()
        
        # MLX is great for local inference on Apple Silicon
        if "mlx" in available_backends:
            # Some models work better with MLX
            mlx_preferred_families = ["llama", "phi", "gemma", "qwen", "mistral"]
            if model_family in mlx_preferred_families:
                return "mlx"
        
        # Ollama is good for ease of use
        if "ollama" in available_backends:
            return "ollama"
    
    # Default to Ollama for cross-platform compatibility
    return "ollama"


def validate_backend_compatibility(backend: str, model_id: str) -> Tuple[bool, Optional[str]]:
    """Validate if a model is compatible with a backend."""
    try:
        validate_model_name(model_id)
    except Exception as e:
        return False, f"Invalid model ID: {e}"
    
    if backend == "ollama":
        # Ollama has broad compatibility
        return True, None
    
    elif backend == "mlx":
        # MLX requires Apple Silicon
        system_info = get_system_info()
        if not (system_info.get('architecture') == 'arm64' and system_info.get('platform') == 'Darwin'):
            return False, "MLX backend requires Apple Silicon (M1/M2/M3/M4)"
        
        # Check if model ID looks like MLX format
        if not (model_id.startswith("mlx-community/") or "/" in model_id):
            return False, "MLX models should use HuggingFace-style paths (e.g., mlx-community/model-name)"
        
        return True, None
    
    return False, f"Unknown backend: {backend}"


def merge_model_lists(lists: Dict[str, List[ModelInfo]]) -> List[ModelInfo]:
    """Merge model lists from multiple backends, removing duplicates."""
    seen_ids = set()
    merged = []
    
    for backend_name, models in lists.items():
        for model in models:
            # Create unique key based on model characteristics
            key = (model.id.lower(), model.family, model.size)
            
            if key not in seen_ids:
                seen_ids.add(key)
                merged.append(model)
            else:
                # If we've seen this model, prefer the installed version
                for i, existing in enumerate(merged):
                    existing_key = (existing.id.lower(), existing.family, existing.size)
                    if existing_key == key and model.installed and not existing.installed:
                        merged[i] = model
                        break
    
    return merged


def filter_models_by_criteria(
    models: List[ModelInfo],
    family: Optional[str] = None,
    max_size_gb: Optional[float] = None,
    installed_only: bool = False,
    format_filter: Optional[str] = None
) -> List[ModelInfo]:
    """Filter models by various criteria."""
    filtered = []
    
    for model in models:
        # Family filter
        if family and model.family != family:
            continue
        
        # Size filter (rough estimation)
        if max_size_gb and model.size:
            try:
                # Extract numeric size for comparison
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', model.size)
                if match:
                    size_num = float(match.group(1))
                    # Rough conversion to GB (assuming parameters)
                    if 'B' in model.size.upper():
                        size_gb = size_num * 2  # Rough estimate: 2GB per billion parameters
                    elif 'M' in model.size.upper():
                        size_gb = size_num * 0.002  # 2MB per million parameters
                    else:
                        size_gb = size_num
                    
                    if size_gb > max_size_gb:
                        continue
            except:
                pass
        
        # Installation filter
        if installed_only and not model.installed:
            continue
        
        # Format filter
        if format_filter and model.format != format_filter:
            continue
        
        filtered.append(model)
    
    return filtered


def get_model_capabilities(model_info: ModelInfo) -> List[str]:
    """Infer model capabilities from model information."""
    capabilities = []
    
    if not model_info.family:
        return capabilities
    
    family = model_info.family.lower()
    model_id = model_info.id.lower()
    name = model_info.name.lower()
    
    # Text generation (most models)
    capabilities.append("text-generation")
    
    # Chat capabilities
    if any(keyword in model_id or keyword in name for keyword in ["chat", "instruct", "assistant"]):
        capabilities.append("chat")
    
    # Code capabilities
    if any(keyword in model_id or keyword in name for keyword in ["code", "programming", "coder"]):
        capabilities.append("code-generation")
    
    # Embedding capabilities
    if any(keyword in model_id or keyword in name for keyword in ["embed", "embedding", "sentence"]):
        capabilities.append("embedding")
    
    # Language-specific capabilities
    if "python" in model_id or "python" in name:
        capabilities.append("python")
    
    # Model family specific capabilities
    family_capabilities = {
        "llama": ["chat", "instruction-following"],
        "phi": ["chat", "reasoning"],
        "gemma": ["chat", "safety"],
        "qwen": ["multilingual", "chat"],
        "mistral": ["chat", "instruction-following"],
        "deepseek": ["code-generation", "reasoning"],
    }
    
    if family in family_capabilities:
        capabilities.extend(family_capabilities[family])
    
    # Remove duplicates and return
    return list(set(capabilities))


def create_model_summary(models: List[ModelInfo]) -> Dict[str, Any]:
    """Create a summary of model collection."""
    summary = {
        "total_models": len(models),
        "installed_models": sum(1 for m in models if m.installed),
        "available_models": sum(1 for m in models if not m.installed),
        "families": {},
        "formats": {},
        "capabilities": {},
    }
    
    for model in models:
        # Count by family
        family = model.family or "unknown"
        summary["families"][family] = summary["families"].get(family, 0) + 1
        
        # Count by format
        format_type = model.format or "unknown"
        summary["formats"][format_type] = summary["formats"].get(format_type, 0) + 1
        
        # Count capabilities
        capabilities = get_model_capabilities(model)
        for capability in capabilities:
            summary["capabilities"][capability] = summary["capabilities"].get(capability, 0) + 1
    
    return summary