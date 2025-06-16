"""Environment validation and setup for ehAye Local."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .exceptions import EnvironmentError, VirtualEnvironmentError
from .logging import get_logger

logger = get_logger("environment")


class EnvironmentValidator:
    """Validates and manages environment setup."""
    
    def __init__(self):
        self.python_path = sys.executable
        self.project_root = Path.cwd()
    
    def check_virtual_environment(self) -> bool:
        """Check if running in correct virtual environment."""
        # Check if in any virtual environment
        in_venv = (
            hasattr(sys, 'real_prefix') or 
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            'VIRTUAL_ENV' in os.environ or 
            'CONDA_DEFAULT_ENV' in os.environ
        )
        
        if not in_venv:
            raise VirtualEnvironmentError(
                "Not running in a virtual environment. "
                "Run: source .venv/bin/activate"
            )
        
        # Check if using correct Python executable
        try:
            current_python = subprocess.check_output(
                ['which', 'python'], text=True
            ).strip()
            expected_python = str(self.project_root / ".venv" / "bin" / "python")
            
            if current_python != expected_python:
                logger.debug(
                    f"Python path mismatch: {current_python} != {expected_python}"
                )
                
        except subprocess.CalledProcessError:
            logger.debug("Cannot determine Python path")
        
        return True
    
    def validate_python_version(self, min_version: tuple = (3, 10)) -> bool:
        """Validate Python version meets requirements."""
        current_version = sys.version_info[:2]
        
        if current_version < min_version:
            raise EnvironmentError(
                f"Python {min_version[0]}.{min_version[1]}+ required, "
                f"got {current_version[0]}.{current_version[1]}"
            )
        
        logger.debug(f"Python version OK: {sys.version}")
        return True
    
    def check_required_packages(self, packages: List[str]) -> Dict[str, bool]:
        """Check if required packages are installed."""
        results = {}
        
        for package in packages:
            try:
                __import__(package.replace('-', '_'))
                results[package] = True
                logger.debug(f"Package {package} is available")
            except ImportError:
                results[package] = False
                logger.warning(f"Package {package} not found")
        
        return results
    
    def setup_environment_variables(self, env_vars: Dict[str, str]) -> None:
        """Set up required environment variables."""
        for var, value in env_vars.items():
            # Expand paths
            expanded_value = os.path.expanduser(value)
            os.environ[var] = expanded_value
            logger.debug(f"Set {var}={expanded_value}")
    
    def create_directories(self, directories: List[Path]) -> None:
        """Create required directories."""
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def validate_system_resources(
        self, 
        min_memory_gb: float = 4.0,
        min_disk_gb: float = 10.0
    ) -> bool:
        """Validate system has sufficient resources."""
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb < min_memory_gb:
                raise EnvironmentError(
                    f"Insufficient memory: {available_gb:.1f}GB available, "
                    f"{min_memory_gb}GB required"
                )
            
            # Disk check
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024**3)
            
            if free_gb < min_disk_gb:
                raise EnvironmentError(
                    f"Insufficient disk space: {free_gb:.1f}GB free, "
                    f"{min_disk_gb}GB required"
                )
            
            logger.debug(
                f"Resources OK: {available_gb:.1f}GB RAM, {free_gb:.1f}GB disk"
            )
            return True
            
        except ImportError:
            logger.warning("psutil not available, skipping resource check")
            return True
    
    def get_gpu_info(self) -> Optional[Dict[str, str]]:
        """Get GPU information for macOS."""
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'iogpu.wired_limit_mb'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                gpu_mb = int(result.stdout.strip())
                return {
                    "memory_mb": str(gpu_mb),
                    "memory_gb": f"{gpu_mb/1024:.1f}"
                }
        except (subprocess.CalledProcessError, ValueError):
            pass
        
        return None
    
    def validate_all(self, config: Dict) -> bool:
        """Run all validation checks."""
        logger.info("Validating environment...")
        
        try:
            # Core checks
            self.validate_python_version()
            self.check_virtual_environment()
            
            # Resource checks
            self.validate_system_resources()
            
            # Package checks
            required_packages = config.get('required_packages', [])
            if required_packages:
                missing = [
                    pkg for pkg, available in 
                    self.check_required_packages(required_packages).items()
                    if not available
                ]
                
                if missing:
                    logger.warning(f"Missing packages: {', '.join(missing)}")
            
            # Environment setup
            env_vars = config.get('environment_variables', {})
            if env_vars:
                self.setup_environment_variables(env_vars)
            
            # Directory setup
            directories = config.get('directories', [])
            if directories:
                self.create_directories([Path(d) for d in directories])
            
            logger.info("Environment validation passed")
            return True
            
        except (EnvironmentError, VirtualEnvironmentError) as e:
            logger.error(f"Environment validation failed: {e}")
            raise