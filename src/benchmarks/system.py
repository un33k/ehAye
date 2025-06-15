"""System resource monitoring for benchmarks."""

import time
from typing import Dict, List, Optional

from ..core.exceptions import SystemResourceError
from ..core.logging import get_logger

logger = get_logger("benchmarks.system")


class SystemMonitor:
    """Monitors system resources during benchmarks."""
    
    def __init__(self):
        self.process = None
        self._init_monitoring()
    
    def _init_monitoring(self) -> None:
        """Initialize system monitoring."""
        try:
            import psutil
            self.process = psutil.Process()
            logger.debug("System monitoring initialized")
        except ImportError:
            logger.warning("psutil not available - system monitoring limited")
    
    def check_system_requirements(
        self,
        min_memory_gb: float = 4.0,
        min_disk_gb: float = 10.0
    ) -> bool:
        """Check if system meets benchmark requirements."""
        if not self.process:
            logger.warning("Cannot check requirements - psutil not available")
            return True
        
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb < min_memory_gb:
                raise SystemResourceError(
                    f"Insufficient memory: {available_gb:.1f}GB available, "
                    f"{min_memory_gb}GB required"
                )
            
            # Disk space check
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024**3)
            
            if free_gb < min_disk_gb:
                raise SystemResourceError(
                    f"Insufficient disk space: {free_gb:.1f}GB free, "
                    f"{min_disk_gb}GB required"
                )
            
            logger.debug(f"System requirements OK: {available_gb:.1f}GB RAM, {free_gb:.1f}GB disk")
            return True
            
        except SystemResourceError:
            raise
        except Exception as e:
            logger.error(f"Error checking system requirements: {e}")
            return True  # Assume OK if check fails
    
    def get_memory_info(self) -> Dict[str, float]:
        """Get detailed memory information."""
        if not self.process:
            return {"process_mb": 0, "available_gb": 0, "total_gb": 0, "used_percent": 0}
        
        try:
            import psutil
            
            # Process memory
            process_memory = self.process.memory_info().rss / (1024**2)
            
            # System memory
            memory = psutil.virtual_memory()
            
            return {
                "process_mb": process_memory,
                "available_gb": memory.available / (1024**3),
                "total_gb": memory.total / (1024**3),
                "used_percent": memory.percent
            }
            
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {"process_mb": 0, "available_gb": 0, "total_gb": 0, "used_percent": 0}
    
    def get_cpu_info(self) -> Dict[str, any]:
        """Get CPU information."""
        info = {"count": 0, "count_logical": 0, "usage_percent": 0, "brand": "Unknown"}
        
        try:
            import psutil
            
            info.update({
                "count": psutil.cpu_count(logical=False),
                "count_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=1)
            })
            
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
        
        # Get CPU brand (macOS)
        try:
            import subprocess
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["brand"] = result.stdout.strip()
        except:
            pass
        
        return info
    
    def get_gpu_info(self) -> Dict[str, any]:
        """Get GPU information (macOS specific)."""
        info = {"memory_mb": None, "memory_gb": None, "available": False}
        
        try:
            import subprocess
            
            # Get GPU memory allocation
            result = subprocess.run(
                ['sysctl', '-n', 'iogpu.wired_limit_mb'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                memory_mb = int(result.stdout.strip())
                info.update({
                    "memory_mb": memory_mb,
                    "memory_gb": memory_mb / 1024,
                    "available": True
                })
                
        except Exception as e:
            logger.debug(f"GPU info not available: {e}")
        
        return info
    
    def monitor_benchmark(self, duration_seconds: float = 60) -> Dict[str, List[float]]:
        """Monitor system resources during benchmark."""
        if not self.process:
            return {"timestamps": [], "memory_mb": [], "cpu_percent": []}
        
        try:
            import psutil
            
            timestamps = []
            memory_readings = []
            cpu_readings = []
            
            start_time = time.time()
            
            while time.time() - start_time < duration_seconds:
                current_time = time.time() - start_time
                
                # Memory usage
                memory_mb = self.process.memory_info().rss / (1024**2)
                
                # CPU usage
                cpu_percent = psutil.cpu_percent()
                
                timestamps.append(current_time)
                memory_readings.append(memory_mb)
                cpu_readings.append(cpu_percent)
                
                time.sleep(0.5)  # Sample every 500ms
            
            return {
                "timestamps": timestamps,
                "memory_mb": memory_readings,
                "cpu_percent": cpu_readings
            }
            
        except Exception as e:
            logger.error(f"Error monitoring benchmark: {e}")
            return {"timestamps": [], "memory_mb": [], "cpu_percent": []}
    
    def validate_benchmark_environment(self) -> bool:
        """Validate that the environment is suitable for benchmarks."""
        try:
            # Check basic requirements
            self.check_system_requirements()
            
            # Check that monitoring is working
            memory_info = self.get_memory_info()
            if memory_info["process_mb"] == 0:
                logger.warning("Process memory monitoring not working")
            
            cpu_info = self.get_cpu_info()
            logger.debug(f"CPU info: {cpu_info}")
            
            gpu_info = self.get_gpu_info()
            if gpu_info["available"]:
                logger.debug(f"GPU available: {gpu_info['memory_gb']:.1f}GB")
            else:
                logger.debug("GPU not detected or not available")
            
            return True
            
        except SystemResourceError as e:
            logger.error(f"System validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            return False
    
    def get_thermal_state(self) -> Optional[str]:
        """Get thermal state (macOS specific)."""
        try:
            import subprocess
            result = subprocess.run(
                ['pmset', '-g', 'thermstate'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'nominal' in output:
                    return "nominal"
                elif 'fair' in output:
                    return "fair" 
                elif 'serious' in output:
                    return "serious"
                elif 'critical' in output:
                    return "critical"
            
            return None
            
        except Exception:
            return None


# Global system monitor
system_monitor = SystemMonitor()


def check_system_requirements(min_memory_gb: float = 4.0, min_disk_gb: float = 10.0) -> bool:
    """Check if system meets benchmark requirements."""
    return system_monitor.check_system_requirements(min_memory_gb, min_disk_gb)


def get_system_info() -> Dict[str, any]:
    """Get comprehensive system information."""
    memory_info = system_monitor.get_memory_info()
    cpu_info = system_monitor.get_cpu_info()
    gpu_info = system_monitor.get_gpu_info()
    
    return {
        "memory": memory_info,
        "cpu": cpu_info,
        "gpu": gpu_info,
        "thermal_state": system_monitor.get_thermal_state()
    }


def validate_benchmark_environment() -> bool:
    """Validate benchmark environment."""
    return system_monitor.validate_benchmark_environment()