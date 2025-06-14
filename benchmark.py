#!/usr/bin/env python3
"""
MLX Performance Benchmark
Usage: python benchmark.py [--model MODEL] [--tokens N] [--runs N]
"""

import time
import psutil
import argparse
import sys
import os

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

from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler
from pathlib import Path

def get_system_info():
    """Get system information for benchmark context"""
    memory = psutil.virtual_memory()
    
    info = {
        "total_memory_gb": round(memory.total / (1024**3), 1),
        "available_memory_gb": round(memory.available / (1024**3), 1),
        "cpu_count": psutil.cpu_count(),
        "cpu_count_logical": psutil.cpu_count(logical=True)
    }
    
    # Try to get GPU memory info
    try:
        import subprocess
        result = subprocess.run(['sysctl', '-n', 'iogpu.wired_limit_mb'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            info["gpu_memory_mb"] = int(result.stdout.strip())
    except:
        info["gpu_memory_mb"] = None
    
    # Try to get chip info
    try:
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            info["chip"] = result.stdout.strip()
    except:
        info["chip"] = "Unknown"
    
    return info

def benchmark_model(model_name, num_tokens=100, num_runs=3, prompts=None):
    """Benchmark a specific model with detailed metrics"""
    print(f"🔥 Benchmarking: {model_name}")
    print(f"   Tokens per run: {num_tokens}")
    print(f"   Number of runs: {num_runs}")
    
    if prompts is None:
        prompts = [
            "The future of artificial intelligence is",
            "Write a Python function that",
            "Explain quantum computing in simple terms:",
            "What are the benefits of renewable energy?",
            "Describe the process of photosynthesis:"
        ]
    
    # Get initial memory usage
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024**2)
    
    # Load model and measure time
    print("🔄 Loading model...")
    start_time = time.time()
    try:
        model, tokenizer = load(model_name)
        load_time = time.time() - start_time
    except Exception as e:
        print(f"❌ Failed to load {model_name}: {e}")
        return None
    
    # Memory after loading
    post_load_memory = process.memory_info().rss / (1024**2)
    model_memory = post_load_memory - initial_memory
    
    print(f"✅ Model loaded in {load_time:.2f}s")
    print(f"📊 Model memory usage: {model_memory:.1f}MB")
    
    # Benchmark generation
    results = []
    peak_memory = post_load_memory
    
    for run in range(num_runs):
        prompt = prompts[run % len(prompts)]
        print(f"\n🚀 Run {run + 1}/{num_runs}: {prompt[:50]}...")
        
        # Memory before generation
        pre_gen_memory = process.memory_info().rss / (1024**2)
        
        start_time = time.time()
        try:
            # Create sampler with temperature
            sampler = make_sampler(temp=0.7)
            
            response = generate(
                model, tokenizer,
                prompt=prompt,
                max_tokens=num_tokens,
                sampler=sampler,
                verbose=False
            )
            generation_time = time.time() - start_time
            
            # Memory after generation
            post_gen_memory = process.memory_info().rss / (1024**2)
            peak_memory = max(peak_memory, post_gen_memory)
            
            # Calculate metrics
            actual_tokens = len(response.split()) * 1.3  # Rough token estimate
            tokens_per_second = actual_tokens / generation_time if generation_time > 0 else 0
            
            result = {
                "run": run + 1,
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "generation_time": generation_time,
                "tokens_generated": actual_tokens,
                "tokens_per_second": tokens_per_second,
                "memory_used": post_gen_memory - pre_gen_memory,
                "response_length": len(response)
            }
            
            results.append(result)
            
            print(f"   ⚡ {generation_time:.2f}s | {tokens_per_second:.1f} tokens/sec | {len(response)} chars")
            
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            results.append({
                "run": run + 1,
                "error": str(e),
                "generation_time": 0,
                "tokens_per_second": 0
            })
    
    # Calculate summary statistics
    successful_runs = [r for r in results if "error" not in r]
    
    if not successful_runs:
        print("❌ All benchmark runs failed")
        return None
    
    avg_generation_time = sum(r["generation_time"] for r in successful_runs) / len(successful_runs)
    avg_tokens_per_sec = sum(r["tokens_per_second"] for r in successful_runs) / len(successful_runs)
    max_tokens_per_sec = max(r["tokens_per_second"] for r in successful_runs)
    min_tokens_per_sec = min(r["tokens_per_second"] for r in successful_runs)
    
    total_memory_used = peak_memory - initial_memory
    
    benchmark_result = {
        "model_name": model_name,
        "system_info": get_system_info(),
        "load_time": load_time,
        "model_memory_mb": model_memory,
        "total_memory_mb": total_memory_used,
        "peak_memory_mb": peak_memory,
        "successful_runs": len(successful_runs),
        "total_runs": num_runs,
        "avg_generation_time": avg_generation_time,
        "avg_tokens_per_second": avg_tokens_per_sec,
        "max_tokens_per_second": max_tokens_per_sec,
        "min_tokens_per_second": min_tokens_per_sec,
        "runs": results
    }
    
    return benchmark_result

def print_benchmark_results(result):
    """Print formatted benchmark results"""
    if not result:
        return
    
    print(f"\n📊 Benchmark Results for {result['model_name']}")
    print("=" * 60)
    
    # System info
    sys_info = result["system_info"]
    print(f"🖥️  System: {sys_info['chip']}")
    print(f"💾 Memory: {sys_info['total_memory_gb']}GB total, {sys_info['available_memory_gb']}GB available")
    print(f"🧠 CPU: {sys_info['cpu_count']} cores ({sys_info['cpu_count_logical']} logical)")
    if sys_info.get("gpu_memory_mb"):
        print(f"🎮 GPU: {sys_info['gpu_memory_mb']}MB allocated")
    
    print(f"\n🚀 Performance Metrics:")
    print(f"   Model load time: {result['load_time']:.2f}s")
    print(f"   Model memory usage: {result['model_memory_mb']:.1f}MB")
    print(f"   Peak memory usage: {result['peak_memory_mb']:.1f}MB")
    print(f"   Successful runs: {result['successful_runs']}/{result['total_runs']}")
    
    print(f"\n⚡ Generation Performance:")
    print(f"   Average: {result['avg_tokens_per_second']:.1f} tokens/sec")
    print(f"   Maximum: {result['max_tokens_per_second']:.1f} tokens/sec")
    print(f"   Minimum: {result['min_tokens_per_second']:.1f} tokens/sec")
    print(f"   Avg time: {result['avg_generation_time']:.2f}s")
    
    # Performance rating
    avg_tps = result['avg_tokens_per_second']
    if avg_tps > 100:
        rating = "🚀 Excellent"
    elif avg_tps > 50:
        rating = "⚡ Good"
    elif avg_tps > 20:
        rating = "✅ Acceptable"
    else:
        rating = "⚠️  Slow"
    
    print(f"\n🎯 Performance Rating: {rating}")
    
    # Memory efficiency
    memory_per_token = result['model_memory_mb'] / result['avg_tokens_per_second'] if result['avg_tokens_per_second'] > 0 else 0
    print(f"📈 Memory efficiency: {memory_per_token:.2f} MB per token/sec")

def compare_models(models, num_tokens=100, num_runs=2):
    """Compare multiple models"""
    print(f"🏁 Comparing {len(models)} models")
    print("=" * 60)
    
    results = []
    
    for i, model in enumerate(models):
        print(f"\n📋 Testing {i+1}/{len(models)}: {model}")
        result = benchmark_model(model, num_tokens, num_runs)
        if result:
            results.append(result)
        print("-" * 40)
    
    if not results:
        print("❌ No successful benchmarks")
        return
    
    # Sort by tokens per second
    results.sort(key=lambda x: x['avg_tokens_per_second'], reverse=True)
    
    print(f"\n🏆 Model Comparison Results")
    print("=" * 80)
    print(f"{'Rank':<4} {'Model':<45} {'Tokens/sec':<12} {'Memory':<10} {'Rating'}")
    print("-" * 80)
    
    for i, result in enumerate(results):
        model_name = result['model_name'].split('/')[-1][:40]  # Shorten name
        tps = result['avg_tokens_per_second']
        memory = f"{result['model_memory_mb']:.0f}MB"
        
        if tps > 100:
            rating = "🚀"
        elif tps > 50:
            rating = "⚡"
        elif tps > 20:
            rating = "✅"
        else:
            rating = "⚠️"
        
        print(f"{i+1:<4} {model_name:<45} {tps:<12.1f} {memory:<10} {rating}")
    
    print("\n💡 Recommendations:")
    if results:
        best = results[0]
        print(f"   🥇 Fastest: {best['model_name']} ({best['avg_tokens_per_second']:.1f} tokens/sec)")
        
        # Find most memory efficient
        memory_efficient = min(results, key=lambda x: x['model_memory_mb'])
        print(f"   💾 Most efficient: {memory_efficient['model_name']} ({memory_efficient['model_memory_mb']:.0f}MB)")

def get_installed_models():
    """Get list of actually installed models"""
    models = []
    models_dir = Path.home() / ".mlx-cache" / "models"
    
    if not models_dir.exists():
        return models
    
    for category in ["tiny", "small", "medium", "large"]:
        category_dir = models_dir / category
        model_list_file = category_dir / ".model_list"
        
        if model_list_file.exists() and model_list_file.stat().st_size > 0:
            with open(model_list_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("model_id:"):
                        model_id = line.replace("model_id:", "")
                        models.append(model_id)
    
    return models

def extract_model_size(model_name):
    """Extract model size from model name and format it"""
    import re
    
    # Look for size patterns like "1.5B", "7B", "8B", etc.
    size_patterns = [
        r'(\d+\.\d+)[Bb]',  # Matches "1.5B", "2.7B"
        r'(\d+)[Bb]',       # Matches "7B", "8B", "70B"
    ]
    
    for pattern in size_patterns:
        match = re.search(pattern, model_name)
        if match:
            size_num = match.group(1)
            return f"({size_num}B)"
    
    return None

def parse_model_selection(choice_input, available_models):
    """Parse user selection input - supports single numbers, ranges (1-3), and lists (1,2,4)"""
    max_choice = len(available_models) + 1
    selected_models = []
    
    # Handle special case for "compare all"
    if choice_input.strip() == str(max_choice):
        return available_models
    
    try:
        # Split by commas for list input
        parts = [part.strip() for part in choice_input.split(',')]
        
        for part in parts:
            if '-' in part and part.count('-') == 1:
                # Range input like "1-3"
                start_str, end_str = part.split('-')
                start = int(start_str.strip())
                end = int(end_str.strip())
                
                if start < 1 or end > len(available_models) or start > end:
                    print(f"⚠️  Invalid range: {part} (valid: 1-{len(available_models)})")
                    return []
                
                # Add models in range
                for i in range(start, end + 1):
                    model = available_models[i - 1]
                    if model not in selected_models:
                        selected_models.append(model)
                        
            else:
                # Single number
                choice_num = int(part)
                
                if choice_num == max_choice:
                    # Compare all available
                    return available_models
                elif 1 <= choice_num <= len(available_models):
                    model = available_models[choice_num - 1]
                    if model not in selected_models:
                        selected_models.append(model)
                else:
                    print(f"⚠️  Invalid choice: {choice_num} (valid: 1-{len(available_models)} or {max_choice} for all)")
                    return []
        
        return selected_models
        
    except ValueError:
        print("⚠️  Invalid format. Use numbers (1), ranges (1-3), or lists (1,2,4)")
        return []

def main():
    parser = argparse.ArgumentParser(description="MLX Performance Benchmark")
    parser.add_argument("--model", 
                       help="Specific model to benchmark")
    parser.add_argument("--models", nargs="+",
                       help="Multiple models to compare")
    parser.add_argument("--tokens", type=int, default=100,
                       help="Tokens to generate per run")
    parser.add_argument("--runs", type=int, default=3,
                       help="Number of benchmark runs")
    parser.add_argument("--compare", action="store_true",
                       help="Compare popular models")
    
    args = parser.parse_args()
    
    # Get actually installed models
    installed_models = get_installed_models()
    
    if not installed_models:
        print("❌ No models found!")
        print("💡 To install models:")
        print("   ./install-llm.sh -s <pattern>  # Search models")
        print("   ./install-llm.sh -d <number>   # Download by number")
        return 1
    
    # Use installed models as default
    default_models = installed_models[:4]  # Use first 4 installed models
    
    if args.compare or args.models:
        if args.models:
            # Validate that provided models are installed
            missing_models = [m for m in args.models if m not in installed_models]
            if missing_models:
                print(f"❌ Models not installed: {', '.join(missing_models)}")
                print("💡 Available models:")
                for model in installed_models:
                    print(f"   {model}")
                return 1
            models = args.models
        else:
            models = default_models
        compare_models(models, args.tokens, args.runs)
    elif args.model:
        result = benchmark_model(args.model, args.tokens, args.runs)
        print_benchmark_results(result)
    else:
        # Interactive model selection
        print("🤖 Available models for benchmarking:")
        available_models = installed_models
        
        for i, model in enumerate(available_models):
            # Extract size from model name
            size_info = extract_model_size(model)
            model_display = f"{size_info} {model}" if size_info else model
            print(f"   {i+1}. {model_display}")
        print(f"   {len(available_models)+1}. Compare all available")
        print("\n💡 Selection examples:")
        print("   1      - Benchmark single model")
        print("   1-3    - Compare models 1 through 3")
        print("   1,3,4  - Compare specific models 1, 3, and 4")
        print(f"   {len(available_models)+1}      - Compare all models")
        print("   q      - Quit benchmark")
        
        try:
            choice_input = input(f"\nSelect model(s) (1-{len(available_models)+1}, ranges like 1-3, lists like 1,3,4, or 'q' to quit): ").strip()
            
            # Check for quit
            if choice_input.lower() in ['q', 'quit', 'exit']:
                print("👋 Goodbye!")
                return 0
            
            selected_models = parse_model_selection(choice_input, available_models)
            
            if not selected_models:
                print("❌ Invalid selection")
                return 1
            elif len(selected_models) == 1:
                # Single model benchmark
                model = selected_models[0]
                result = benchmark_model(model, args.tokens, args.runs)
                print_benchmark_results(result)
            else:
                # Multiple model comparison
                compare_models(selected_models, args.tokens, args.runs)
                
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Benchmark cancelled")
            return 1

if __name__ == "__main__":
    sys.exit(main())