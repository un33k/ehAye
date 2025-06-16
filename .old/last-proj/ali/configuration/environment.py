"""Environment management and validation."""

import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..logging import get_logger

logger = get_logger("config.environment")


class EnvironmentManager:
    """Manages environment variables and system validation."""
    
    def __init__(self):
        self._original_env: Dict[str, str] = {}
    
    def set_variables(self, variables: Dict[str, str], backup: bool = True) -> None:
        """Set environment variables with optional backup."""
        if backup:
            # Backup current values
            for key in variables:
                if key in os.environ:
                    self._original_env[key] = os.environ[key]
        
        # Set new values
        for key, value in variables.items():
            os.environ[key] = value
            logger.debug(f"Set environment variable: {key}={value}")
    
    def restore_variables(self) -> None:
        """Restore backed up environment variables."""
        for key, value in self._original_env.items():
            os.environ[key] = value
            logger.debug(f"Restored environment variable: {key}={value}")
        
        self._original_env.clear()
    
    def validate_python_version(self, min_version: Tuple[int, int] = (3, 10)) -> bool:
        """Validate Python version meets requirements."""
        current_version = sys.version_info[:2]
        if current_version < min_version:
            logger.error(f"Python {min_version[0]}.{min_version[1]}+ required, got {current_version[0]}.{current_version[1]}")
            return False
        return True
    
    def validate_virtual_environment(self) -> bool:
        """Validate that we're running in a virtual environment."""
        venv_path = os.environ.get('VIRTUAL_ENV')
        if not venv_path:
            logger.error("No virtual environment detected")
            return False
        
        if '.venv' not in venv_path:
            logger.warning(f"Virtual environment path may not be local: {venv_path}")
        
        return True
    
    def get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_executable": sys.executable,
            "virtual_env": os.environ.get('VIRTUAL_ENV', 'None'),
        }
    
    def check_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon."""
        return platform.system() == "Darwin" and platform.machine() in ["arm64", "arm64e"]
    
    def get_optimal_thread_count(self) -> int:
        """Get optimal thread count for the system."""
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            
            if self.check_apple_silicon():
                # On Apple Silicon, use fewer threads to avoid thermal throttling
                return min(cpu_count - 2, 8)
            else:
                # On other systems, use most available cores
                return max(cpu_count - 1, 1)
        except Exception:
            logger.warning("Could not determine CPU count, using default")
            return 4
    
    def setup_mlx_environment(self, cache_dir: Path, models_dir: Path) -> None:
        """Set up MLX-specific environment variables."""
        mlx_vars = {
            "MLX_CACHE_DIR": str(cache_dir / "mlx"),
            "MLX_MODELS_DIR": str(models_dir),
            "MLX_MEMORY_POOL": "1",  # Enable memory pooling by default
        }
        
        self.set_variables(mlx_vars)
    
    def setup_huggingface_environment(self, cache_dir: Path) -> None:
        """Set up Hugging Face environment variables."""
        hf_vars = {
            "HF_HOME": str(cache_dir / "huggingface"),
            "TRANSFORMERS_CACHE": str(cache_dir / "transformers"),
            "HF_HUB_CACHE": str(cache_dir / "huggingface" / "hub"),
        }
        
        self.set_variables(hf_vars)
    
    def validate_dependencies(self, required_packages: Optional[List[str]] = None) -> Dict[str, bool]:
        """Validate that required packages are available."""
        if required_packages is None:
            required_packages = ["rich", "typer", "pydantic", "toml"]
        
        results = {}
        for package in required_packages:
            try:
                __import__(package)
                results[package] = True
                logger.debug(f"Package {package}: OK")
            except ImportError:
                results[package] = False
                logger.warning(f"Package {package}: MISSING")
        
        return results