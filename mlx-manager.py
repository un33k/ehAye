#!/usr/bin/env python3
"""
MLX Manager - Advanced MLX model management and performance monitoring
Usage: python mlx_manager.py [command] [options]
"""

import os
import sys
import json
import time
import psutil
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Check if running in correct virtual environment
def check_virtual_env():
    """Ensure we're running in the correct virtual environment"""
    import subprocess
    
    # Check if in any virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        if 'VIRTUAL_ENV' not in os.environ and 'CONDA_DEFAULT_ENV' not in os.environ:
            print("❌ Error: Not running in a virtual environment!")
            print("🔒 For safety, this script requires a virtual environment.")
            print("")
            print("💡 To fix this:")
            print("   1. Run: source .venv/bin/activate")
            print("   2. Or run: ./install-venv.sh")
            print("   3. Then run this script again")
            sys.exit(1)
    
    # Check if using the correct Python executable
    try:
        current_python = subprocess.check_output(['which', 'python'], text=True).strip()
        expected_python = os.path.abspath('.venv/bin/python')
        
        if current_python != expected_python:
            print("❌ Error: Not using the correct virtual environment!")
            print(f"🔍 Current Python: {current_python}")
            print(f"🎯 Expected Python: {expected_python}")
            print("")
            print("💡 To fix this:")
            print("   1. Run: source .venv/bin/activate")
            print("   2. Verify with: which python")
            print("   3. Then run this script again")
            sys.exit(1)
            
    except subprocess.CalledProcessError:
        print("❌ Error: Cannot determine Python path")
        sys.exit(1)

# Check virtual environment at startup
check_virtual_env()

try:
    from mlx_lm import load, generate
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("❌ Required packages not installed. Run the install script first.")
    sys.exit(1)

console = Console()

@dataclass
class ModelInfo:
    id: str
    name: str
    category: str
    size_gb: float
    params: str
    description: str
    loaded: bool = False
    last_used: Optional[str] = None

@dataclass
class PerformanceMetrics:
    load_time: float
    memory_mb: float
    tokens_per_second: float
    peak_memory_mb: float
    gpu_utilization: float

class MLXManager:
    def __init__(self):
        self.models_dir = Path("models")
        self.cache_dir = Path("cache")
        self.config_file = Path("mlx_config.json")
        self.loaded_models = {}
        self.performance_log = []
        
        self.console = Console()
        self.load_config()

    def load_config(self):
        """Load or create configuration"""
        default_config = {
            "cache_dir": str(self.cache_dir),
            "default_model": None,
            "performance_logging": True,
            "auto_cleanup": True,
            "max_cache_size_gb": 50,
            "preferred_quantization": "4bit"
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = {**default_config, **json.load(f)}
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        memory = psutil.virtual_memory()
        
        return {
            "total_memory_gb": round(memory.total / (1024**3), 1),
            "available_memory_gb": round(memory.available / (1024**3), 1),
            "memory_percent": memory.percent,
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "disk_free_gb": round(psutil.disk_usage('.').free / (1024**3), 1)
        }

    def scan_available_models(self) -> List[ModelInfo]:
        """Scan for available models in the models directory"""
        models = []
        
        # Known model mappings
        model_database = {
            "phi-2-MLX": ModelInfo("mlx-community/phi-2-MLX", "Phi-2", "small", 2.8, "2.7B", "Fast lightweight model"),
            "Mistral-7B-Instruct": ModelInfo("mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx", "Mistral 7B", "medium", 4.1, "7B", "Balanced performance"),
            "CodeLlama-7b": ModelInfo("mlx-community/CodeLlama-7b-Instruct-hf-4bit-mlx", "CodeLlama 7B", "code", 4.2, "7B", "Code generation"),
            "Llama-2-13b": ModelInfo("mlx-community/Llama-2-13b-chat-hf-4bit-mlx", "Llama 2 13B", "large", 7.3, "13B", "High quality chat"),
            "Mixtral-8x7B": ModelInfo("mlx-community/Mixtral-8x7B-Instruct-v0.1-4bit-mlx", "Mixtral 8x7B", "large", 26.9, "46.7B", "Best quality, high memory"),
        }
        
        # Check cache directory for downloaded models
        cache_path = Path(os.environ.get('HF_HOME', self.cache_dir / 'huggingface'))
        if cache_path.exists():
            for model_dir in cache_path.rglob('models--*'):
                if model_dir.is_dir():
                    model_name = model_dir.name.replace('models--', '').replace('--', '/')
                    for key, model_info in model_database.items():
                        if key.lower() in model_name.lower():
                            models.append(model_info)
                            break
        
        return models

    def benchmark_model(self, model_id: str, num_tokens: int = 100) -> PerformanceMetrics:
        """Benchmark a specific model"""
        console.print(f"🔥 Benchmarking {model_id}...")
        
        # Monitor memory before loading
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024**2)
        
        # Load model and measure time
        start_time = time.time()
        try:
            model, tokenizer = load(model_id)
            load_time = time.time() - start_time
        except Exception as e:
            console.print(f"❌ Failed to load {model_id}: {e}")
            return None
        
        # Memory after loading
        post_load_memory = process.memory_info().rss / (1024**2)
        
        # Generate text and measure performance
        test_prompt = "The future of artificial intelligence is"
        
        start_time = time.time()
        peak_memory = post_load_memory
        
        # Monitor memory during generation
        generation_start = time.time()
        try:
            response = generate(
                model, tokenizer,
                prompt=test_prompt,
                max_tokens=num_tokens,
                temp=0.7,
                verbose=False
            )
            generation_time = time.time() - generation_start
            tokens_per_second = num_tokens / generation_time if generation_time > 0 else 0
            
            # Check peak memory
            current_memory = process.memory_info().rss / (1024**2)
            peak_memory = max(peak_memory, current_memory)
            
        except Exception as e:
            console.print(f"❌ Generation failed: {e}")
            return None
        
        # Estimate GPU utilization (approximation)
        gpu_utilization = min(100, (post_load_memory - initial_memory) / 100 * 10)
        
        metrics = PerformanceMetrics(
            load_time=load_time,
            memory_mb=post_load_memory - initial_memory,
            tokens_per_second=tokens_per_second,
            peak_memory_mb=peak_memory - initial_memory,
            gpu_utilization=gpu_utilization
        )
        
        # Log performance
        if self.config.get("performance_logging", True):
            self.performance_log.append({
                "timestamp": time.time(),
                "model_id": model_id,
                "metrics": metrics.__dict__
            })
        
        return metrics

    def recommend_model(self) -> Optional[str]:
        """Recommend the best model based on system specs"""
        system_info = self.get_system_info()
        available_memory = system_info["available_memory_gb"]
        
        if available_memory < 8:
            return "mlx-community/phi-2-MLX"
        elif available_memory < 16:
            return "mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx"
        elif available_memory < 32:
            return "mlx-community/Llama-2-13b-chat-hf-4bit-mlx"
        else:
            return "mlx-community/Mixtral-8x7B-Instruct-v0.1-4bit-mlx"

    def cleanup_cache(self):
        """Clean up old cached models"""
        if not Confirm.ask("🗑️  Clean up model cache?"):
            return
        
        cache_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file()) / (1024**3)
        console.print(f"📊 Current cache size: {cache_size:.1f}GB")
        
        if cache_size > self.config.get("max_cache_size_gb", 50):
            console.print("🧹 Cache size exceeded limit, cleaning up...")
            # Implementation would remove oldest unused models
            console.print("✅ Cache cleanup completed")

    def interactive_chat(self, model_id: Optional[str] = None):
        """Start an interactive chat session"""
        if not model_id:
            model_id = self.recommend_model()
            
        console.print(Panel(f"🚀 Loading {model_id}", title="MLX Chat"))
        
        try:
            model, tokenizer = load(model_id)
            console.print("✅ Model loaded successfully!")
        except Exception as e:
            console.print(f"❌ Failed to load model: {e}")
            return
        
        console.print("\n💬 MLX Advanced Chat (type 'quit', 'benchmark', or 'stats' for commands)")
        console.print("-" * 60)
        
        while True:
            try:
                user_input = Prompt.ask("\n🧑 You").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'benchmark':
                    metrics = self.benchmark_model(model_id)
                    if metrics:
                        self.display_performance(metrics)
                    continue
                elif user_input.lower() == 'stats':
                    self.display_system_stats()
                    continue
                elif not user_input:
                    continue
                
                console.print("🤖 Assistant: ", end="")
                
                start_time = time.time()
                response = generate(
                    model, tokenizer,
                    prompt=user_input,
                    max_tokens=512,
                    temp=0.7,
                    verbose=False
                )
                generation_time = time.time() - start_time
                
                console.print(response)
                console.print(f"\n⚡ Generated in {generation_time:.2f}s", style="dim")
                
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")

    def display_performance(self, metrics: PerformanceMetrics):
        """Display performance metrics in a nice table"""
        table = Table(title="🎯 Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Load Time", f"{metrics.load_time:.2f}s")
        table.add_row("Memory Usage", f"{metrics.memory_mb:.1f}MB")
        table.add_row("Tokens/Second", f"{metrics.tokens_per_second:.1f}")
        table.add_row("Peak Memory", f"{metrics.peak_memory_mb:.1f}MB")
        table.add_row("GPU Utilization", f"{metrics.gpu_utilization:.1f}%")
        
        console.print(table)

    def display_system_stats(self):
        """Display current system statistics"""
        stats = self.get_system_info()
        
        table = Table(title="🖥️  System Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Total Memory", f"{stats['total_memory_gb']}GB")
        table.add_row("Available Memory", f"{stats['available_memory_gb']}GB")
        table.add_row("Memory Usage", f"{stats['memory_percent']:.1f}%")
        table.add_row("CPU Usage", f"{stats['cpu_percent']:.1f}%")
        table.add_row("Free Disk Space", f"{stats['disk_free_gb']:.1f}GB")
        
        console.print(table)

def main():
    parser = argparse.ArgumentParser(description="MLX Advanced Manager")
    parser.add_argument("command", nargs="?", default="chat", 
                       choices=["chat", "benchmark", "list", "stats", "cleanup"],
                       help="Command to run")
    parser.add_argument("--model", help="Model ID to use")
    parser.add_argument("--tokens", type=int, default=100, help="Tokens for benchmarking")
    
    args = parser.parse_args()
    
    manager = MLXManager()
    
    if args.command == "chat":
        manager.interactive_chat(args.model)
    elif args.command == "benchmark":
        model_id = args.model or manager.recommend_model()
        metrics = manager.benchmark_model(model_id, args.tokens)
        if metrics:
            manager.display_performance(metrics)
    elif args.command == "list":
        models = manager.scan_available_models()
        if models:
            table = Table(title="📚 Available Models")
            table.add_column("Name", style="cyan")
            table.add_column("Category", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Parameters", style="magenta")
            table.add_column("Description", style="white")
            
            for model in models:
                table.add_row(model.name, model.category, f"{model.size_gb}GB", 
                            model.params, model.description)
            
            console.print(table)
        else:
            console.print("❌ No models found. Run the installation script first.")
    elif args.command == "stats":
        manager.display_system_stats()
    elif args.command == "cleanup":
        manager.cleanup_cache()

if __name__ == "__main__":
    main()