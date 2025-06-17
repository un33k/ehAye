"""Configuration management for ehAye."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError("tomli is required for Python < 3.11. Install with: pip install tomli")

from pydantic import BaseModel, Field, validator

from ..exceptions.base import ConfigurationError
from ..logging.logger import get_logger

logger = get_logger("config")


class PathConfig(BaseModel):
    """Path configuration."""
    cache_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ehaye")
    models_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ehaye" / "models")
    logs_dir: Path = Field(default_factory=lambda: Path.home() / ".cache" / "ehaye" / "logs")
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".config" / "ehaye")
    
    @validator('*', pre=True)
    def expand_paths(cls, v):
        if isinstance(v, (str, Path)):
            return Path(v).expanduser().resolve()
        return v


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    omp_num_threads: int = 8
    mlx_memory_pool: bool = True
    performance_logging: bool = False
    max_cache_size_gb: int = 50
    gpu_memory_fraction: float = 0.8


class ModelConfig(BaseModel):
    """Model configuration."""
    categories: List[str] = ["tiny", "small", "medium", "large", "code"]
    default_model: Optional[str] = None
    preferred_quantization: str = "4bit"
    auto_cleanup: bool = True
    max_models_cached: int = 10
    default_backend: str = "ollama"  # "ollama" or "mlx"
    backends: List[str] = ["ollama", "mlx"]


class CLIConfig(BaseModel):
    """CLI configuration."""
    main_command: str = "ali"
    model_command: str = "mod"
    chat_command: str = "chat"
    performance_command: str = "perf"
    system_command: str = "sys"
    ollama_command: str = "olla"

class ChatConfig(BaseModel):
    """Chat configuration."""
    default_temperature: float = 0.7
    default_max_tokens: int = 512
    streaming_enabled: bool = True
    history_length: int = 1000
    save_conversations: bool = True


class BenchmarkConfig(BaseModel):
    """Benchmark configuration."""
    default_runs: int = 3
    default_tokens: int = 100
    timeout_seconds: int = 300
    save_results: bool = True


class EhAyeConfig(BaseModel):
    """Main configuration class."""
    paths: PathConfig = Field(default_factory=PathConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    models: ModelConfig = Field(default_factory=ModelConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    chat: ChatConfig = Field(default_factory=ChatConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    
    @property
    def environment_variables(self) -> Dict[str, str]:
        """Get environment variables to set."""
        return {
            "MLX_CACHE_DIR": str(self.paths.cache_dir / "mlx"),
            "MLX_MODELS_DIR": str(self.paths.models_dir),
            "HF_HOME": str(self.paths.cache_dir / "huggingface"),
            "TRANSFORMERS_CACHE": str(self.paths.cache_dir / "transformers"),
            "OMP_NUM_THREADS": str(self.performance.omp_num_threads),
            "MLX_MEMORY_POOL": "1" if self.performance.mlx_memory_pool else "0",
        }
    
    def create_directories(self) -> None:
        """Create all configured directories."""
        directories = [
            self.paths.cache_dir,
            self.paths.models_dir,
            self.paths.logs_dir,
            self.paths.config_dir,
        ]
        
        # Create model category subdirectories
        for category in self.models.categories:
            directories.append(self.paths.models_dir / category)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def setup_environment(self) -> None:
        """Set up environment variables and directories."""
        # Set environment variables
        for var, value in self.environment_variables.items():
            os.environ[var] = value
            logger.debug(f"Set {var}={value}")
        
        # Create directories
        self.create_directories()
    
    def get_model_list_file(self, category: str) -> Path:
        """Get path to model list file for a category."""
        return self.paths.models_dir / category / ".model_list"


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("config/settings.toml")
        self._config: Optional[EhAyeConfig] = None
    
    def load(self, config_file: Optional[Path] = None) -> EhAyeConfig:
        """Load configuration from file."""
        if config_file:
            self.config_file = config_file
        
        if not self.config_file.exists():
            logger.debug(f"Config file {self.config_file} not found, using defaults")
            self._config = EhAyeConfig()
            return self._config
        
        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)
            
            self._config = EhAyeConfig(**config_data)
            logger.debug(f"Loaded configuration from {self.config_file}")
            return self._config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")
    
    def save(self, config_file: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if not self._config:
            raise ConfigurationError("No configuration to save")
        
        save_file = config_file or self.config_file
        save_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import toml
            with open(save_file, 'w') as f:
                toml.dump(self._config.dict(), f)
            logger.debug(f"Saved configuration to {save_file}")
        except ImportError:
            logger.warning("toml package not available, cannot save config")
    
    @property
    def config(self) -> EhAyeConfig:
        """Get the current configuration."""
        if not self._config:
            return self.load()
        return self._config
    
    def update(self, **kwargs) -> None:
        """Update configuration values."""
        if not self._config:
            self.load()
        
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")


# Global config manager
config_manager = ConfigManager()


def get_config() -> EhAyeConfig:
    """Get the global configuration."""
    return config_manager.config


def load_config(config_file: Optional[Path] = None) -> EhAyeConfig:
    """Load configuration from file."""
    return config_manager.load(config_file)