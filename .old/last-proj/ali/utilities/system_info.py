"""System information utilities."""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import warnings

from ..logging import get_logger

logger = get_logger("utilities.system")


class SystemInfo:
    """Collects and manages system information."""
    
    def __init__(self):
        self._cached_info: Optional[Dict[str, Any]] = None
    
    @property
    def info(self) -> Dict[str, Any]:
        """Get cached system information."""
        if self._cached_info is None:
            self._cached_info = self._collect_system_info()
        return self._cached_info
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect comprehensive system information."""
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'platform_release': platform.release(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'python_executable': sys.executable,
            'python_path': sys.path[0] if sys.path else None,
        }
        
        # Virtual environment info
        info.update(self._get_venv_info())
        
        # Memory and disk info
        info.update(self._get_resource_info())
        
        # Apple Silicon specific info
        if self.is_apple_silicon():
            info.update(self._get_apple_silicon_info())
        
        # GPU info
        gpu_info = self._get_gpu_info()
        if gpu_info:
            info['gpu'] = gpu_info
        
        return info
    
    def _get_venv_info(self) -> Dict[str, Any]:
        """Get virtual environment information."""
        venv_info = {
            'virtual_env': os.environ.get('VIRTUAL_ENV'),
            'conda_env': os.environ.get('CONDA_DEFAULT_ENV'),
            'in_virtualenv': self._check_virtualenv(),
        }
        
        # Detect venv type
        if venv_info['virtual_env']:
            venv_info['venv_type'] = 'venv'
        elif venv_info['conda_env']:
            venv_info['venv_type'] = 'conda'
        else:
            venv_info['venv_type'] = 'none'
        
        return venv_info
    
    def _check_virtualenv(self) -> bool:
        """Check if running in a virtual environment."""
        return (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
            'VIRTUAL_ENV' in os.environ or
            'CONDA_DEFAULT_ENV' in os.environ
        )
    
    def _get_resource_info(self) -> Dict[str, Any]:
        """Get system resource information."""
        resource_info = {}
        
        try:
            import psutil
            
            # Memory info
            memory = psutil.virtual_memory()
            resource_info['memory'] = {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
            }
            
            # Disk info for current directory
            disk = psutil.disk_usage('.')
            resource_info['disk'] = {
                'total': disk.total,
                'free': disk.free,
                'used': disk.used,
                'percent': round((disk.used / disk.total) * 100, 1),
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
            }
            
            # CPU info
            resource_info['cpu'] = {
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True),
                'percent': psutil.cpu_percent(interval=1),
            }
            
        except ImportError:
            logger.debug("psutil not available, limited resource info")
            resource_info['memory'] = {'error': 'psutil not available'}
            resource_info['disk'] = {'error': 'psutil not available'}
            resource_info['cpu'] = {'error': 'psutil not available'}
        
        return resource_info
    
    def _get_apple_silicon_info(self) -> Dict[str, Any]:
        """Get Apple Silicon specific information."""
        info = {}
        
        try:
            # Get system info
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info['cpu_brand'] = result.stdout.strip()
            
            # Get GPU info
            gpu_info = self._get_gpu_memory_macos()
            if gpu_info:
                info.update(gpu_info)
            
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            logger.debug("Could not get Apple Silicon info")
        
        return info
    
    def _get_gpu_memory_macos(self) -> Optional[Dict[str, Any]]:
        """Get GPU memory information on macOS."""
        try:
            # Try to get GPU memory limit
            result = subprocess.run(
                ['sysctl', '-n', 'iogpu.wired_limit_mb'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                gpu_mb = int(result.stdout.strip())
                return {
                    'gpu_memory_mb': gpu_mb,
                    'gpu_memory_gb': round(gpu_mb / 1024, 2),
                }
        except (subprocess.SubprocessError, ValueError, subprocess.TimeoutExpired):
            pass
        
        return None
    
    def _get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU information for the current platform."""
        if platform.system() == "Darwin":
            return self._get_gpu_memory_macos()
        
        # Could add NVIDIA/AMD GPU detection here for other platforms
        return None
    
    def is_apple_silicon(self) -> bool:
        """Check if running on Apple Silicon."""
        return (
            platform.system() == "Darwin" and 
            platform.machine() in ["arm64", "arm64e"]
        )
    
    def is_mlx_compatible(self) -> bool:
        """Check if system is compatible with MLX."""
        return self.is_apple_silicon()
    
    def get_optimal_thread_count(self) -> int:
        """Get optimal thread count for the system."""
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            
            if self.is_apple_silicon():
                # On Apple Silicon, use fewer threads to avoid thermal throttling
                return min(cpu_count - 2, 8)
            else:
                # On other systems, use most available cores
                return max(cpu_count - 1, 1)
        except Exception:
            logger.warning("Could not determine CPU count, using default")
            return 4
    
    def check_dependencies(self, packages: List[str]) -> Dict[str, bool]:
        """Check if required packages are available."""
        results = {}
        
        for package in packages:
            try:
                # Handle packages with dashes
                import_name = package.replace('-', '_')
                __import__(import_name)
                results[package] = True
                logger.debug(f"Package {package}: Available")
            except ImportError:
                results[package] = False
                logger.debug(f"Package {package}: Missing")
        
        return results
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate the current environment."""
        validation = {
            'python_version_ok': sys.version_info >= (3, 10),
            'in_virtualenv': self._check_virtualenv(),
            'sufficient_memory': True,  # Default
            'sufficient_disk': True,    # Default
        }
        
        # Check memory and disk if psutil available
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            validation['sufficient_memory'] = memory.available > 4 * (1024**3)  # 4GB
            validation['sufficient_disk'] = disk.free > 10 * (1024**3)  # 10GB
            
        except ImportError:
            pass
        
        validation['overall_ok'] = all([
            validation['python_version_ok'],
            validation['in_virtualenv'],
            validation['sufficient_memory'],
            validation['sufficient_disk'],
        ])
        
        return validation
    
    def get_environment_summary(self) -> str:
        """Get a human-readable environment summary."""
        info = self.info
        
        summary_parts = [
            f"Platform: {info['platform']} {info['architecture']}",
            f"Python: {info['python_version']}",
        ]
        
        if info.get('virtual_env'):
            summary_parts.append(f"Virtual Env: {Path(info['virtual_env']).name}")
        
        if 'memory' in info and isinstance(info['memory'], dict):
            if 'available_gb' in info['memory']:
                summary_parts.append(f"Memory: {info['memory']['available_gb']}GB available")
        
        if self.is_apple_silicon():
            summary_parts.append("Apple Silicon: Yes")
            
            if 'gpu_memory_gb' in info:
                summary_parts.append(f"GPU Memory: {info['gpu_memory_gb']}GB")
        
        return " | ".join(summary_parts)


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    return SystemInfo().info


def check_apple_silicon() -> bool:
    """Check if running on Apple Silicon."""
    return SystemInfo().is_apple_silicon()


def get_optimal_threads() -> int:
    """Get optimal thread count for the current system."""
    return SystemInfo().get_optimal_thread_count()


def validate_system_requirements(
    min_memory_gb: float = 4.0,
    min_disk_gb: float = 10.0,
    required_packages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Validate system meets requirements."""
    system = SystemInfo()
    validation = system.validate_environment()
    
    if required_packages:
        package_results = system.check_dependencies(required_packages)
        validation['required_packages'] = package_results
        validation['packages_ok'] = all(package_results.values())
        validation['overall_ok'] = validation['overall_ok'] and validation['packages_ok']
    
    return validation