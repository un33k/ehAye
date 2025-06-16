"""Configuration utility functions."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..logging import get_logger

logger = get_logger("config.utils")


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configuration dictionaries recursively."""
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def validate_config_paths(config: Dict[str, Any]) -> List[str]:
    """Validate that all path configurations are valid."""
    errors = []
    
    def check_path_section(section_name: str, paths_dict: Dict[str, Any]) -> None:
        for path_name, path_value in paths_dict.items():
            if isinstance(path_value, (str, Path)):
                try:
                    path = Path(path_value).expanduser()
                    # Check if parent directory is writable
                    if not path.parent.exists():
                        path.parent.mkdir(parents=True, exist_ok=True)
                    elif not os.access(path.parent, os.W_OK):
                        errors.append(f"{section_name}.{path_name}: Parent directory not writable: {path.parent}")
                except Exception as e:
                    errors.append(f"{section_name}.{path_name}: Invalid path '{path_value}': {e}")
    
    # Check paths section
    if "paths" in config:
        check_path_section("paths", config["paths"])
    
    return errors


def expand_config_paths(config: Dict[str, Any]) -> Dict[str, Any]:
    """Expand all path values in configuration."""
    result = config.copy()
    
    def expand_paths_recursive(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {key: expand_paths_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [expand_paths_recursive(item) for item in obj]
        elif isinstance(obj, (str, Path)) and ("/" in str(obj) or "\\" in str(obj)):
            # Likely a path, expand it
            try:
                return str(Path(obj).expanduser().resolve())
            except Exception:
                return obj
        else:
            return obj
    
    return expand_paths_recursive(result)


def get_config_schema() -> Dict[str, Any]:
    """Get the configuration schema for validation."""
    return {
        "paths": {
            "cache_dir": {"type": "path", "required": False},
            "models_dir": {"type": "path", "required": False},
            "logs_dir": {"type": "path", "required": False},
            "config_dir": {"type": "path", "required": False},
        },
        "performance": {
            "omp_num_threads": {"type": "int", "min": 1, "max": 32},
            "mlx_memory_pool": {"type": "bool"},
            "performance_logging": {"type": "bool"},
            "max_cache_size_gb": {"type": "int", "min": 1},
            "gpu_memory_fraction": {"type": "float", "min": 0.1, "max": 1.0},
        },
        "models": {
            "categories": {"type": "list", "items": "str"},
            "default_model": {"type": "str", "required": False},
            "preferred_quantization": {"type": "str"},
            "auto_cleanup": {"type": "bool"},
            "max_models_cached": {"type": "int", "min": 1},
            "default_backend": {"type": "str", "choices": ["ollama", "mlx"]},
            "backends": {"type": "list", "items": "str"},
        },
        "chat": {
            "default_temperature": {"type": "float", "min": 0.0, "max": 2.0},
            "default_max_tokens": {"type": "int", "min": 1},
            "streaming_enabled": {"type": "bool"},
            "history_length": {"type": "int", "min": 0},
            "save_conversations": {"type": "bool"},
        },
        "benchmark": {
            "default_runs": {"type": "int", "min": 1},
            "default_tokens": {"type": "int", "min": 1},
            "timeout_seconds": {"type": "int", "min": 1},
            "save_results": {"type": "bool"},
        },
    }


def validate_config_values(config: Dict[str, Any]) -> List[str]:
    """Validate configuration values against schema."""
    schema = get_config_schema()
    errors = []
    
    def validate_section(section_name: str, section_data: Dict[str, Any], section_schema: Dict[str, Any]) -> None:
        for key, value in section_data.items():
            if key not in section_schema:
                logger.warning(f"Unknown config key: {section_name}.{key}")
                continue
            
            field_schema = section_schema[key]
            field_type = field_schema.get("type")
            
            # Type validation
            if field_type == "int" and not isinstance(value, int):
                errors.append(f"{section_name}.{key}: Expected int, got {type(value).__name__}")
                continue
            elif field_type == "float" and not isinstance(value, (int, float)):
                errors.append(f"{section_name}.{key}: Expected float, got {type(value).__name__}")
                continue
            elif field_type == "bool" and not isinstance(value, bool):
                errors.append(f"{section_name}.{key}: Expected bool, got {type(value).__name__}")
                continue
            elif field_type == "str" and not isinstance(value, str):
                errors.append(f"{section_name}.{key}: Expected str, got {type(value).__name__}")
                continue
            elif field_type == "list" and not isinstance(value, list):
                errors.append(f"{section_name}.{key}: Expected list, got {type(value).__name__}")
                continue
            
            # Range validation
            if field_type in ["int", "float"]:
                if "min" in field_schema and value < field_schema["min"]:
                    errors.append(f"{section_name}.{key}: Value {value} below minimum {field_schema['min']}")
                if "max" in field_schema and value > field_schema["max"]:
                    errors.append(f"{section_name}.{key}: Value {value} above maximum {field_schema['max']}")
            
            # Choice validation
            if "choices" in field_schema and value not in field_schema["choices"]:
                errors.append(f"{section_name}.{key}: Value '{value}' not in allowed choices: {field_schema['choices']}")
    
    # Validate each section
    for section_name, section_schema in schema.items():
        if section_name in config:
            validate_section(section_name, config[section_name], section_schema)
    
    return errors