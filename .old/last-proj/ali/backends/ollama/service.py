"""Ollama service management utilities."""

import subprocess
import time
import psutil
from typing import Optional, Dict, Any
from pathlib import Path

from ...exceptions import OllamaServiceError, BackendError
from ...logging import get_logger

logger = get_logger("backends.ollama.service")


class OllamaService:
    """Manages Ollama service lifecycle."""
    
    def __init__(self, host: str = "localhost", port: int = 11434):
        self.host = host
        self.port = port
        self.service_url = f"http://{host}:{port}"
    
    def is_running(self) -> bool:
        """Check if Ollama service is running."""
        try:
            import requests
            response = requests.get(f"{self.service_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def start(self, background: bool = True, timeout: float = 30) -> bool:
        """Start Ollama service."""
        if self.is_running():
            logger.info("Ollama service already running")
            return True
        
        try:
            if background:
                # Start as background process
                process = subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                
                # Wait for service to be ready
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if self.is_running():
                        logger.info(f"Ollama service started successfully (PID: {process.pid})")
                        return True
                    time.sleep(0.5)
                
                # If we get here, service didn't start in time
                try:
                    process.terminate()
                except:
                    pass
                
                raise OllamaServiceError(f"Service did not start within {timeout} seconds")
            
            else:
                # Start in foreground (blocking)
                result = subprocess.run(["ollama", "serve"], check=True)
                return result.returncode == 0
                
        except FileNotFoundError:
            raise OllamaServiceError("Ollama executable not found. Please install Ollama first.")
        except subprocess.CalledProcessError as e:
            raise OllamaServiceError(f"Failed to start Ollama service: {e}")
        except Exception as e:
            raise BackendError(f"Error starting Ollama service: {e}", backend_name="ollama", cause=e)
    
    def stop(self, timeout: float = 10) -> bool:
        """Stop Ollama service."""
        try:
            # Find Ollama processes
            ollama_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        if proc.info['cmdline'] and any('serve' in arg for arg in proc.info['cmdline']):
                            ollama_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not ollama_processes:
                logger.info("No Ollama service processes found")
                return True
            
            # Terminate processes gracefully
            for proc in ollama_processes:
                try:
                    logger.info(f"Terminating Ollama process {proc.pid}")
                    proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Wait for graceful shutdown
            _, still_running = psutil.wait_procs(ollama_processes, timeout=timeout)
            
            # Force kill if necessary
            for proc in still_running:
                try:
                    logger.warning(f"Force killing Ollama process {proc.pid}")
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Verify service is stopped
            time.sleep(1)
            if not self.is_running():
                logger.info("Ollama service stopped successfully")
                return True
            else:
                logger.warning("Ollama service may still be running")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping Ollama service: {e}")
            return False
    
    def restart(self, timeout: float = 30) -> bool:
        """Restart Ollama service."""
        logger.info("Restarting Ollama service")
        
        if self.is_running():
            if not self.stop(timeout=10):
                logger.error("Failed to stop Ollama service for restart")
                return False
        
        return self.start(timeout=timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        status = {
            "running": self.is_running(),
            "url": self.service_url,
            "processes": [],
            "version": None,
        }
        
        # Get version if available
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                status["version"] = result.stdout.strip()
        except Exception:
            pass
        
        # Get process information
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        status["processes"].append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cmdline": proc.info['cmdline'],
                            "memory_mb": proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0,
                            "cpu_percent": proc.info['cpu_percent'],
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f"Could not get process info: {e}")
        
        return status
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "service_running": False,
            "api_responsive": False,
            "models_accessible": False,
            "disk_space_ok": True,
            "memory_usage": None,
            "errors": [],
        }
        
        try:
            # Check if service is running
            health["service_running"] = self.is_running()
            
            if health["service_running"]:
                # Test API responsiveness
                import requests
                try:
                    response = requests.get(f"{self.service_url}/api/tags", timeout=5)
                    health["api_responsive"] = response.status_code == 200
                    
                    if health["api_responsive"]:
                        # Test model listing
                        data = response.json()
                        health["models_accessible"] = "models" in data
                        
                except requests.RequestException as e:
                    health["errors"].append(f"API not responsive: {e}")
            
            # Check disk space (rough estimate)
            try:
                import shutil
                total, used, free = shutil.disk_usage(Path.home())
                free_gb = free / (1024**3)
                health["disk_space_ok"] = free_gb > 5.0  # At least 5GB free
                if not health["disk_space_ok"]:
                    health["errors"].append(f"Low disk space: {free_gb:.1f}GB free")
            except Exception as e:
                health["errors"].append(f"Could not check disk space: {e}")
            
            # Check memory usage
            status = self.get_status()
            if status["processes"]:
                total_memory = sum(p["memory_mb"] for p in status["processes"])
                health["memory_usage"] = f"{total_memory:.1f}MB"
        
        except Exception as e:
            health["errors"].append(f"Health check error: {e}")
        
        return health
    
    def wait_for_ready(self, timeout: float = 30, check_interval: float = 0.5) -> bool:
        """Wait for service to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.is_running():
                # Additional check - try to list models
                try:
                    import requests
                    response = requests.get(f"{self.service_url}/api/tags", timeout=2)
                    if response.status_code == 200:
                        return True
                except:
                    pass
            
            time.sleep(check_interval)
        
        return False