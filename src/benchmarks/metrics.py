"""Performance metrics collection and calculation."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..core.logging import get_logger

logger = get_logger("benchmarks.metrics")


@dataclass
class BenchmarkResult:
    """Single benchmark run result."""
    run_id: int
    prompt: str
    response: str
    generation_time: float
    tokens_generated: int
    tokens_per_second: float
    memory_before_mb: float
    memory_after_mb: float
    memory_used_mb: float
    success: bool
    error: Optional[str] = None


@dataclass
class ModelBenchmarkSummary:
    """Summary of all benchmark runs for a model."""
    model_id: str
    model_name: str
    load_time: float
    model_memory_mb: float
    total_memory_mb: float
    peak_memory_mb: float
    successful_runs: int
    total_runs: int
    avg_generation_time: float
    avg_tokens_per_second: float
    max_tokens_per_second: float
    min_tokens_per_second: float
    results: List[BenchmarkResult]
    system_info: Dict[str, any]


class MetricsCollector:
    """Collects and calculates performance metrics."""
    
    def __init__(self):
        self.process = None
        self._init_process_monitor()
    
    def _init_process_monitor(self) -> None:
        """Initialize process monitoring."""
        try:
            import psutil
            self.process = psutil.Process()
        except ImportError:
            logger.warning("psutil not available, memory monitoring disabled")
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if not self.process:
            return 0.0
        
        try:
            return self.process.memory_info().rss / (1024**2)
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return 0.0
    
    def get_system_info(self) -> Dict[str, any]:
        """Get system information for benchmark context."""
        info = {
            "total_memory_gb": 0,
            "available_memory_gb": 0,
            "cpu_count": 0,
            "cpu_count_logical": 0,
            "gpu_memory_mb": None,
            "chip": "Unknown"
        }
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            info.update({
                "total_memory_gb": round(memory.total / (1024**3), 1),
                "available_memory_gb": round(memory.available / (1024**3), 1),
                "cpu_count": psutil.cpu_count(logical=False),
                "cpu_count_logical": psutil.cpu_count(logical=True)
            })
        except ImportError:
            pass
        
        # Get GPU memory info (macOS)
        try:
            import subprocess
            result = subprocess.run(
                ['sysctl', '-n', 'iogpu.wired_limit_mb'], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["gpu_memory_mb"] = int(result.stdout.strip())
        except:
            pass
        
        # Get chip info (macOS)
        try:
            import subprocess
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'], 
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info["chip"] = result.stdout.strip()
        except:
            pass
        
        return info
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        # Rough estimation: ~1.3 words per token for English
        words = len(text.split())
        return int(words * 1.3)
    
    def create_benchmark_result(
        self,
        run_id: int,
        prompt: str,
        response: str,
        generation_time: float,
        memory_before: float,
        memory_after: float,
        error: Optional[str] = None
    ) -> BenchmarkResult:
        """Create a benchmark result from metrics."""
        tokens_generated = self.estimate_tokens(response)
        tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
        memory_used = memory_after - memory_before
        
        return BenchmarkResult(
            run_id=run_id,
            prompt=prompt,
            response=response,
            generation_time=generation_time,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_per_second,
            memory_before_mb=memory_before,
            memory_after_mb=memory_after,
            memory_used_mb=memory_used,
            success=error is None,
            error=error
        )
    
    def calculate_summary(
        self,
        model_id: str,
        model_name: str,
        load_time: float,
        initial_memory: float,
        peak_memory: float,
        results: List[BenchmarkResult]
    ) -> ModelBenchmarkSummary:
        """Calculate benchmark summary from results."""
        successful_runs = [r for r in results if r.success]
        
        if not successful_runs:
            # Handle case with no successful runs
            return ModelBenchmarkSummary(
                model_id=model_id,
                model_name=model_name,
                load_time=load_time,
                model_memory_mb=0,
                total_memory_mb=peak_memory - initial_memory,
                peak_memory_mb=peak_memory,
                successful_runs=0,
                total_runs=len(results),
                avg_generation_time=0,
                avg_tokens_per_second=0,
                max_tokens_per_second=0,
                min_tokens_per_second=0,
                results=results,
                system_info=self.get_system_info()
            )
        
        # Calculate averages and extremes
        avg_generation_time = sum(r.generation_time for r in successful_runs) / len(successful_runs)
        avg_tokens_per_sec = sum(r.tokens_per_second for r in successful_runs) / len(successful_runs)
        max_tokens_per_sec = max(r.tokens_per_second for r in successful_runs)
        min_tokens_per_sec = min(r.tokens_per_second for r in successful_runs)
        
        # Estimate model memory (difference between initial and first successful run)
        model_memory = 0
        if successful_runs:
            model_memory = successful_runs[0].memory_after_mb - initial_memory
        
        return ModelBenchmarkSummary(
            model_id=model_id,
            model_name=model_name,
            load_time=load_time,
            model_memory_mb=model_memory,
            total_memory_mb=peak_memory - initial_memory,
            peak_memory_mb=peak_memory,
            successful_runs=len(successful_runs),
            total_runs=len(results),
            avg_generation_time=avg_generation_time,
            avg_tokens_per_second=avg_tokens_per_sec,
            max_tokens_per_second=max_tokens_per_sec,
            min_tokens_per_second=min_tokens_per_sec,
            results=results,
            system_info=self.get_system_info()
        )


# Global metrics collector
metrics_collector = MetricsCollector()


def collect_benchmark_metrics(
    run_id: int,
    prompt: str,
    response: str,
    generation_time: float,
    memory_before: float,
    memory_after: float,
    error: Optional[str] = None
) -> BenchmarkResult:
    """Collect metrics for a benchmark run."""
    return metrics_collector.create_benchmark_result(
        run_id, prompt, response, generation_time, 
        memory_before, memory_after, error
    )


def calculate_benchmark_summary(
    model_id: str,
    model_name: str,
    load_time: float,
    initial_memory: float,
    peak_memory: float,
    results: List[BenchmarkResult]
) -> ModelBenchmarkSummary:
    """Calculate benchmark summary."""
    return metrics_collector.calculate_summary(
        model_id, model_name, load_time, initial_memory, peak_memory, results
    )