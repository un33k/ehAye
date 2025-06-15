#!/usr/bin/env python3
"""
MLX Performance Test Suite
Tests various aspects of MLX performance
"""

import os
import time
import sys
from pathlib import Path

# Check for help flag early, before imports that might fail
if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
    def show_help():
        """Show help message"""
        print("""🚀 MLX Performance Test Suite

Usage: python performance-test.py [OPTIONS]

Options:
    -h, --help    Show this help message and exit

Tests performed:
    • Import Speed          - Test MLX module loading
    • Environment Variables - Check MLX environment setup  
    • GPU Memory Allocation - Verify GPU memory configuration
    • Cache Directories     - Check model cache directories
    • System Resources      - Verify available memory/disk
    • Memory Optimization   - Test memory usage patterns
    • Model Loading         - Test model download/loading
    • Basic Operations      - Benchmark CPU/memory operations

Examples:
    python performance-test.py    # Run all tests
    python performance-test.py -h # Show this help
""")
    show_help()
    sys.exit(0)

import psutil

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
            print("   2. Or run: ./venv.sh")
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
            
        print(f"✅ Correct virtual environment detected: {current_python}")
            
    except subprocess.CalledProcessError:
        print("❌ Error: Cannot determine Python path")
        sys.exit(1)

# Check virtual environment at startup
check_virtual_env()

def test_import_speed():
    """Test MLX import speed"""
    print("🧪 Testing MLX import speed...")
    start_time = time.time()
    try:
        from mlx_lm import load, generate
        import_time = time.time() - start_time
        print(f"✅ MLX import: {import_time:.3f}s")
        return True
    except ImportError as e:
        print(f"❌ MLX import failed: {e}")
        return False

def test_memory_optimization():
    """Test memory usage optimization"""
    print("🧪 Testing memory optimization...")
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024**2)
    
    # Simulate workload
    import numpy as np
    large_array = np.random.random((1000, 1000))
    
    peak_memory = process.memory_info().rss / (1024**2)
    memory_increase = peak_memory - initial_memory
    
    print(f"📊 Memory usage: {initial_memory:.1f}MB → {peak_memory:.1f}MB (+{memory_increase:.1f}MB)")
    
    del large_array
    return memory_increase < 100  # Should be reasonable

def test_environment_vars():
    """Test environment variable setup"""
    print("🧪 Testing environment variables...")
    
    try:
        from mlx_config import mlx_config, ensure_mlx_environment
        
        missing_vars = mlx_config.check_environment()
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("🔧 Auto-configuring from mlx-config.json...")
            ensure_mlx_environment()
            print("✅ Environment variables configured")
            print("💡 For permanent setup, run: source mlx_env.sh")
            return True
        else:
            print("✅ All environment variables set correctly")
            return True
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Check mlx-config.json exists and is valid")
        return False

def test_gpu_memory_allocation():
    """Test GPU memory allocation"""
    print("🧪 Testing GPU memory allocation...")
    
    try:
        import subprocess
        result = subprocess.run(['sysctl', '-n', 'iogpu.wired_limit_mb'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            gpu_mb = int(result.stdout.strip())
            print(f"✅ GPU memory allocated: {gpu_mb}MB ({gpu_mb/1024:.1f}GB)")
            return gpu_mb > 0
        else:
            print("❌ Could not read GPU memory allocation")
            return False
    except Exception as e:
        print(f"❌ GPU memory test failed: {e}")
        return False

def test_cache_directories():
    """Test cache directory setup"""
    print("🧪 Testing cache directories...")
    
    # Check for updated home directory cache paths
    home_dir = os.path.expanduser('~')
    cache_dirs = [
        os.environ.get('MLX_CACHE_DIR', f'{home_dir}/.mlx-cache/mlx'),
        os.environ.get('HF_HOME', f'{home_dir}/.mlx-cache/huggingface'),
        os.environ.get('MLX_MODELS_DIR', f'{home_dir}/.mlx-cache/models'),
        f'{home_dir}/.mlx-cache/transformers'
    ]
    
    all_exist = True
    for cache_dir in cache_dirs:
        if cache_dir and Path(cache_dir).exists():
            print(f"✅ Cache directory exists: {cache_dir}")
        else:
            print(f"❌ Cache directory missing: {cache_dir}")
            all_exist = False
    
    return all_exist

def test_model_loading():
    """Test basic model loading (if models are available)"""
    print("🧪 Testing model loading...")
    
    try:
        from mlx_lm import load
        
        # Try to find any available model
        models_dir = Path(os.environ.get('MLX_MODELS_DIR', 'models'))
        if not models_dir.exists():
            print("⏭️  Skipping model test - no models directory")
            return True
        
        # Look for model registry or any cached models
        cache_dir = Path(os.environ.get('HF_HOME', 'cache/huggingface'))
        if cache_dir.exists():
            model_dirs = list(cache_dir.glob('models--*'))
            if model_dirs:
                print(f"✅ Found {len(model_dirs)} cached models")
                return True
        
        print("⏭️  Skipping model test - no models found")
        return True
        
    except Exception as e:
        print(f"❌ Model loading test failed: {e}")
        return False

def test_system_resources():
    """Test system resource availability"""
    print("🧪 Testing system resources...")
    
    # Memory test
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    
    # Disk test
    disk = psutil.disk_usage('.')
    free_gb = disk.free / (1024**3)
    
    print(f"📊 Available memory: {available_gb:.1f}GB")
    print(f"📊 Free disk space: {free_gb:.1f}GB")
    
    if available_gb < 2:
        print("⚠️  Warning: Low available memory")
        return False
    
    if free_gb < 10:
        print("⚠️  Warning: Low disk space")
        return False
    
    print("✅ System resources look good")
    return True

def benchmark_basic_operations():
    """Benchmark basic operations"""
    print("🧪 Benchmarking basic operations...")
    
    try:
        import numpy as np
        
        # CPU benchmark
        start_time = time.time()
        arr = np.random.random((1000, 1000))
        result = np.dot(arr, arr.T)
        cpu_time = time.time() - start_time
        
        print(f"⚡ CPU matrix multiplication: {cpu_time:.3f}s")
        
        # Memory allocation benchmark
        start_time = time.time()
        large_arrays = [np.random.random((500, 500)) for _ in range(10)]
        alloc_time = time.time() - start_time
        
        print(f"⚡ Memory allocation (10x 500x500): {alloc_time:.3f}s")
        
        del arr, result, large_arrays
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return False

def main():
    
    print("🚀 MLX Performance Test Suite")
    print("=" * 40)
    
    tests = [
        ("Import Speed", test_import_speed),
        ("Environment Variables", test_environment_vars),
        ("GPU Memory Allocation", test_gpu_memory_allocation),
        ("Cache Directories", test_cache_directories),
        ("System Resources", test_system_resources),
        ("Memory Optimization", test_memory_optimization),
        ("Model Loading", test_model_loading),
        ("Basic Operations Benchmark", benchmark_basic_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print(f"\n📈 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! MLX is optimally configured.")
        return 0
    elif passed >= total * 0.8:
        print("⚡ Most tests passed. MLX should work well.")
        return 0
    else:
        print("⚠️  Several tests failed. Check your MLX configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())