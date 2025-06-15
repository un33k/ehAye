"""Benchmark execution engine."""

import time
from typing import List, Optional

from ..core.logging import get_logger
from ..llm.generation import GenerationConfig, generate_text
from ..models.loader import load_model
from .metrics import BenchmarkResult, ModelBenchmarkSummary, metrics_collector

logger = get_logger("benchmarks.runner")


class BenchmarkRunner:
    """Executes benchmark runs for models."""
    
    DEFAULT_PROMPTS = [
        "The future of artificial intelligence is",
        "Write a Python function that",
        "Explain quantum computing in simple terms:",
        "What are the benefits of renewable energy?",
        "Describe the process of photosynthesis:",
        "How does machine learning work?",
        "Create a simple web application using",
        "What are the advantages of cloud computing?",
        "Explain the concept of blockchain technology:",
        "Write a story about a robot learning to"
    ]
    
    def __init__(self):
        self.metrics = metrics_collector
    
    def benchmark_model(
        self,
        model_id: str,
        num_tokens: int = 100,
        num_runs: int = 3,
        prompts: Optional[List[str]] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> ModelBenchmarkSummary:
        """Benchmark a specific model."""
        logger.info(f"Starting benchmark for {model_id}")
        
        if prompts is None:
            prompts = self.DEFAULT_PROMPTS
        
        if generation_config is None:
            generation_config = GenerationConfig(max_tokens=num_tokens)
        else:
            generation_config.max_tokens = num_tokens
        
        # Get initial memory
        initial_memory = self.metrics.get_memory_usage()
        peak_memory = initial_memory
        
        # Load model and measure time
        logger.info("Loading model...")
        start_time = time.time()
        
        try:
            model, tokenizer = load_model(model_id)
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            # Return failed summary
            return ModelBenchmarkSummary(
                model_id=model_id,
                model_name=model_id.split('/')[-1],
                load_time=0,
                model_memory_mb=0,
                total_memory_mb=0,
                peak_memory_mb=initial_memory,
                successful_runs=0,
                total_runs=0,
                avg_generation_time=0,
                avg_tokens_per_second=0,
                max_tokens_per_second=0,
                min_tokens_per_second=0,
                results=[],
                system_info=self.metrics.get_system_info()
            )
        
        # Memory after loading
        post_load_memory = self.metrics.get_memory_usage()
        peak_memory = max(peak_memory, post_load_memory)
        
        # Run benchmarks
        results = []
        
        for run in range(num_runs):
            prompt = prompts[run % len(prompts)]
            logger.info(f"Run {run + 1}/{num_runs}: {prompt[:50]}...")
            
            result = self._run_single_benchmark(
                run + 1,
                prompt,
                model_id,
                generation_config
            )
            
            results.append(result)
            peak_memory = max(peak_memory, result.memory_after_mb)
            
            # Log result
            if result.success:
                logger.info(f"  ✅ {result.generation_time:.2f}s | {result.tokens_per_second:.1f} tokens/sec")
            else:
                logger.error(f"  ❌ {result.error}")
        
        # Calculate summary
        model_name = model_id.split('/')[-1] if '/' in model_id else model_id
        summary = self.metrics.calculate_summary(
            model_id=model_id,
            model_name=model_name,
            load_time=load_time,
            initial_memory=initial_memory,
            peak_memory=peak_memory,
            results=results
        )
        
        logger.info(f"Benchmark completed: {summary.successful_runs}/{summary.total_runs} successful")
        return summary
    
    def _run_single_benchmark(
        self,
        run_id: int,
        prompt: str,
        model_id: str,
        generation_config: GenerationConfig
    ) -> BenchmarkResult:
        """Run a single benchmark iteration."""
        memory_before = self.metrics.get_memory_usage()
        
        try:
            start_time = time.time()
            
            response = generate_text(
                prompt=prompt,
                model_id=model_id,
                config=generation_config
            )
            
            generation_time = time.time() - start_time
            memory_after = self.metrics.get_memory_usage()
            
            return self.metrics.create_benchmark_result(
                run_id=run_id,
                prompt=prompt,
                response=response,
                generation_time=generation_time,
                memory_before=memory_before,
                memory_after=memory_after
            )
            
        except Exception as e:
            memory_after = self.metrics.get_memory_usage()
            error_msg = str(e)
            
            return self.metrics.create_benchmark_result(
                run_id=run_id,
                prompt=prompt,
                response="",
                generation_time=0,
                memory_before=memory_before,
                memory_after=memory_after,
                error=error_msg
            )
    
    def compare_models(
        self,
        model_ids: List[str],
        num_tokens: int = 100,
        num_runs: int = 2
    ) -> List[ModelBenchmarkSummary]:
        """Compare multiple models."""
        logger.info(f"Comparing {len(model_ids)} models")
        
        results = []
        
        for i, model_id in enumerate(model_ids):
            logger.info(f"Testing {i+1}/{len(model_ids)}: {model_id}")
            
            try:
                summary = self.benchmark_model(model_id, num_tokens, num_runs)
                results.append(summary)
            except Exception as e:
                logger.error(f"Benchmark failed for {model_id}: {e}")
                continue
        
        # Sort by performance
        results.sort(key=lambda x: x.avg_tokens_per_second, reverse=True)
        
        logger.info(f"Model comparison completed: {len(results)} models benchmarked")
        return results
    
    def validate_environment(self) -> bool:
        """Validate that benchmark environment is ready."""
        try:
            # Check memory monitoring
            memory = self.metrics.get_memory_usage()
            if memory == 0:
                logger.warning("Memory monitoring not available")
            
            # Check system info
            system_info = self.metrics.get_system_info()
            logger.debug(f"System info: {system_info}")
            
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False


# Global benchmark runner
benchmark_runner = BenchmarkRunner()


def benchmark_model(
    model_id: str,
    num_tokens: int = 100,
    num_runs: int = 3,
    prompts: Optional[List[str]] = None
) -> ModelBenchmarkSummary:
    """Benchmark a single model."""
    return benchmark_runner.benchmark_model(model_id, num_tokens, num_runs, prompts)


def compare_models(
    model_ids: List[str],
    num_tokens: int = 100,
    num_runs: int = 2
) -> List[ModelBenchmarkSummary]:
    """Compare multiple models."""
    return benchmark_runner.compare_models(model_ids, num_tokens, num_runs)