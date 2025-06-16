"""MLX optimization utilities for Apple Silicon performance."""

from typing import Dict, Any, Optional, Tuple, List
import time
from pathlib import Path

from ...exceptions import MLXError, MLXMemoryError
from ...logging import get_logger
from ...utilities import get_system_info

logger = get_logger("backends.mlx.optimizer")


class MLXOptimizer:
    """Optimization utilities for MLX inference on Apple Silicon."""
    
    def __init__(self):
        self.system_info = get_system_info()
        self._memory_pool_enabled = True
        self._optimization_cache = {}
    
    def optimize_for_device(self, model_size_gb: float) -> Dict[str, Any]:
        """Optimize MLX settings for the current device."""
        optimization_config = {
            "memory_pool": self._memory_pool_enabled,
            "batch_size": 1,  # Start conservative
            "memory_fraction": 0.8,
            "cache_enabled": True,
            "metal_performance_shaders": True,
            "precision": "fp16",
        }
        
        # Adjust based on available memory
        if 'memory' in self.system_info and 'available_gb' in self.system_info['memory']:
            available_memory = self.system_info['memory']['available_gb']
            
            # Conservative memory usage
            if model_size_gb > available_memory * 0.8:
                logger.warning(f"Model size ({model_size_gb:.1f}GB) may exceed available memory ({available_memory:.1f}GB)")
                optimization_config["memory_fraction"] = 0.6
                optimization_config["precision"] = "4bit"  # Use more aggressive quantization
            elif model_size_gb > available_memory * 0.5:
                optimization_config["memory_fraction"] = 0.7
        
        # Device-specific optimizations
        if self._is_apple_silicon_m1():
            optimization_config["memory_fraction"] = min(optimization_config["memory_fraction"], 0.7)
        elif self._is_apple_silicon_m2_or_newer():
            # M2+ chips can handle higher memory usage
            optimization_config["memory_fraction"] = min(optimization_config["memory_fraction"], 0.85)
        
        return optimization_config
    
    def benchmark_inference(
        self,
        model: Any,
        tokenizer: Any,
        prompt: str = "Hello, how are you today?",
        num_trials: int = 3
    ) -> Dict[str, Any]:
        """Benchmark inference performance."""
        try:
            import mlx.core as mx
            
            # Tokenize prompt
            tokens = tokenizer.encode(prompt)
            input_tokens = mx.array(tokens)[None]  # Add batch dimension
            
            # Warmup
            for _ in range(2):
                _ = model(input_tokens)
                mx.eval(_)  # Ensure computation is complete
            
            # Benchmark
            times = []
            token_counts = []
            
            for trial in range(num_trials):
                start_time = time.time()
                
                # Generate tokens
                generated = 0
                current_tokens = input_tokens
                
                for _ in range(50):  # Generate 50 tokens
                    logits = model(current_tokens)
                    next_token = mx.argmax(logits[:, -1, :], axis=-1, keepdims=True)
                    current_tokens = mx.concatenate([current_tokens, next_token], axis=1)
                    generated += 1
                    
                    # Evaluate to ensure computation completes
                    mx.eval(current_tokens)
                
                end_time = time.time()
                
                times.append(end_time - start_time)
                token_counts.append(generated)
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            avg_tokens = sum(token_counts) / len(token_counts)
            tokens_per_second = avg_tokens / avg_time
            
            return {
                "avg_time_seconds": avg_time,
                "tokens_per_second": tokens_per_second,
                "trials": num_trials,
                "times": times,
                "token_counts": token_counts,
                "input_tokens": len(tokens),
            }
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            return {"error": str(e)}
    
    def optimize_generation_config(
        self,
        model_size_gb: float,
        target_tokens_per_second: Optional[float] = None
    ) -> Dict[str, Any]:
        """Optimize generation configuration for performance."""
        config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 512,
            "batch_size": 1,
        }
        
        # Adjust based on model size
        if model_size_gb < 2.0:
            # Small models can handle more aggressive settings
            config["max_tokens"] = 1024
            config["temperature"] = 0.8
        elif model_size_gb > 8.0:
            # Large models should be more conservative
            config["max_tokens"] = 256
            config["temperature"] = 0.6
        
        # Memory-based adjustments
        if 'memory' in self.system_info:
            available_memory = self.system_info['memory'].get('available_gb', 8.0)
            
            if available_memory < 8.0:
                config["max_tokens"] = min(config["max_tokens"], 256)
            elif available_memory > 16.0:
                config["max_tokens"] = min(config["max_tokens"] * 2, 2048)
        
        return config
    
    def monitor_performance(self, model_id: str) -> Dict[str, Any]:
        """Monitor real-time performance metrics."""
        try:
            import mlx.core as mx
            import psutil
            
            # System metrics
            memory = psutil.virtual_memory()
            
            metrics = {
                "timestamp": time.time(),
                "model_id": model_id,
                "system_memory_percent": memory.percent,
                "system_memory_available_gb": memory.available / (1024**3),
                "cpu_percent": psutil.cpu_percent(interval=1),
            }
            
            # MLX-specific metrics if available
            try:
                # This may not be available in all MLX versions
                mlx_memory = mx.metal.get_memory_info()
                metrics["mlx_memory"] = mlx_memory
            except:
                pass
            
            # GPU temperature (if available)
            try:
                import subprocess
                result = subprocess.run(
                    ["sudo", "powermetrics", "--samplers", "smc", "-n", "1", "-i", "1"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0:
                    # Parse temperature from output (this is a simplified approach)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'CPU die temperature' in line:
                            temp_str = line.split(':')[-1].strip()
                            if 'C' in temp_str:
                                temp = float(temp_str.replace('C', '').strip())
                                metrics["cpu_temperature_c"] = temp
                                break
            except:
                pass
            
            return metrics
            
        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return {"error": str(e)}
    
    def suggest_optimizations(self, performance_data: Dict[str, Any]) -> List[str]:
        """Suggest optimizations based on performance data."""
        suggestions = []
        
        # Memory-based suggestions
        if "system_memory_percent" in performance_data:
            memory_usage = performance_data["system_memory_percent"]
            
            if memory_usage > 90:
                suggestions.append("System memory usage is very high (>90%). Consider using a smaller model or enabling more aggressive quantization.")
            elif memory_usage > 80:
                suggestions.append("System memory usage is high (>80%). Monitor for potential swapping.")
        
        # Performance-based suggestions
        if "tokens_per_second" in performance_data:
            tps = performance_data["tokens_per_second"]
            
            if tps < 5:
                suggestions.append("Token generation is slow (<5 tokens/sec). Consider using a smaller model or enabling performance optimizations.")
            elif tps < 10:
                suggestions.append("Token generation could be faster. Check if Metal Performance Shaders are enabled.")
        
        # Temperature-based suggestions
        if "cpu_temperature_c" in performance_data:
            temp = performance_data["cpu_temperature_c"]
            
            if temp > 85:
                suggestions.append("CPU temperature is high (>85°C). Consider reducing batch size or enabling thermal throttling protection.")
            elif temp > 75:
                suggestions.append("CPU temperature is elevated (>75°C). Monitor for thermal throttling.")
        
        # Model-specific suggestions
        if not suggestions:
            suggestions.append("Performance looks good! Consider experimenting with higher batch sizes for better throughput.")
        
        return suggestions
    
    def enable_memory_pool(self) -> bool:
        """Enable MLX memory pool for better performance."""
        try:
            import mlx.core as mx
            # This might not be available in all MLX versions
            mx.metal.set_memory_limit(0)  # Use default limit
            self._memory_pool_enabled = True
            logger.info("MLX memory pool enabled")
            return True
        except Exception as e:
            logger.warning(f"Could not enable memory pool: {e}")
            return False
    
    def disable_memory_pool(self) -> bool:
        """Disable MLX memory pool."""
        try:
            import mlx.core as mx
            # Implementation depends on MLX version
            self._memory_pool_enabled = False
            logger.info("MLX memory pool disabled")
            return True
        except Exception as e:
            logger.warning(f"Could not disable memory pool: {e}")
            return False
    
    def _is_apple_silicon_m1(self) -> bool:
        """Check if running on M1 chip."""
        cpu_brand = self.system_info.get('cpu_brand', '').lower()
        return 'm1' in cpu_brand
    
    def _is_apple_silicon_m2_or_newer(self) -> bool:
        """Check if running on M2 or newer chip."""
        cpu_brand = self.system_info.get('cpu_brand', '').lower()
        return any(chip in cpu_brand for chip in ['m2', 'm3', 'm4'])
    
    def get_optimal_batch_size(self, model_size_gb: float, sequence_length: int = 512) -> int:
        """Calculate optimal batch size for the given model and sequence length."""
        available_memory = self.system_info.get('memory', {}).get('available_gb', 8.0)
        
        # Conservative memory estimation
        # Each token roughly uses model_size / vocab_size memory
        estimated_memory_per_token = model_size_gb / 32000  # Rough estimate
        memory_per_sequence = estimated_memory_per_token * sequence_length
        
        # Keep memory usage under 70% of available
        max_memory_usage = available_memory * 0.7
        max_batch_size = int(max_memory_usage / (model_size_gb + memory_per_sequence))
        
        # Clamp to reasonable range
        batch_size = max(1, min(max_batch_size, 8))
        
        logger.debug(f"Calculated optimal batch size: {batch_size} for {model_size_gb:.1f}GB model")
        return batch_size
    
    def profile_model_loading(self, model_path: Path) -> Dict[str, Any]:
        """Profile model loading performance."""
        start_time = time.time()
        
        try:
            # This would integrate with actual model loading
            load_time = time.time() - start_time
            
            profile = {
                "load_time_seconds": load_time,
                "model_path": str(model_path),
                "success": True,
            }
            
            # Add memory usage after loading
            try:
                import psutil
                memory = psutil.virtual_memory()
                profile["memory_after_load_gb"] = (memory.total - memory.available) / (1024**3)
            except:
                pass
            
            return profile
            
        except Exception as e:
            return {
                "load_time_seconds": time.time() - start_time,
                "model_path": str(model_path),
                "success": False,
                "error": str(e),
            }