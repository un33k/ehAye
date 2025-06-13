#!/bin/bash
# MLX Advanced Performance Environment Variables
# This file will be dynamically configured during installation

# --- Help Function ---
show_mlx_env_help() {
    cat << EOF
🔥 MLX Environment Configuration

Usage: source mlx-env.sh [OPTIONS]

Description:
    Sets up optimized environment variables for MLX performance.
    This file should be sourced, not executed directly.

Options:
    -h, --help    Show this help message (when executed directly)

Environment Variables Set:
    • MLX_MEMORY_POOL       - Enable memory pooling
    • MLX_LAZY_LOADING      - Enable lazy loading
    • MLX_CACHE_SIZE_MB     - Cache size based on system RAM
    • OMP_NUM_THREADS       - OpenMP thread count
    • MKL_NUM_THREADS       - Intel MKL thread count
    • METAL_*               - Metal Performance Shaders settings
    • HF_HOME               - Hugging Face cache directory (~/.mlx-cache/huggingface)
    • MLX_CACHE_DIR         - MLX cache directory (~/.mlx-cache/mlx)

Examples:
    source mlx-env.sh         # Load MLX optimizations
    ./mlx-env.sh -h          # Show this help
    mlx-env-status           # Check loaded environment

Functions provided:
    • mlx-env-status         - Show current MLX environment status
    • mlx-env-reset          - Reset MLX environment variables
EOF
}

# Handle help when executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        show_mlx_env_help
        return 0 2>/dev/null || exit 0
    fi
    echo "⚠️  This script should be sourced, not executed directly."
    echo "   Run: source mlx-env.sh"
    echo "   Or:  source mlx-env.sh -h for help"
    exit 1
fi

# Core MLX optimizations
export MLX_MEMORY_POOL=1
export MLX_LAZY_LOADING=1
export MLX_CACHE_SIZE_MB=12800  # Will be set based on RAM

# Thread optimization based on your CPU
export OMP_NUM_THREADS=16
export MKL_NUM_THREADS=16
export OPENBLAS_NUM_THREADS=16

# Metal Performance Shaders optimization
export METAL_DEVICE_WRAPPER_TYPE=1
export METAL_PERFORMANCE_SHADERS_FRAMEWORKS=1
export MTL_HUD_ENABLED=1  # Enable Metal HUD for debugging

# Memory management
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Hugging Face cache optimization - moved to user home directory
export HF_HOME="$HOME/.mlx-cache/huggingface"
export HF_HUB_CACHE="$HOME/.mlx-cache/huggingface"
export TRANSFORMERS_CACHE="$HOME/.mlx-cache/transformers"

# MLX specific paths - moved to user home directory
export MLX_CACHE_DIR="$HOME/.mlx-cache/mlx"
export MLX_MODELS_DIR="$HOME/.mlx-cache/models"

# Performance monitoring
export MLX_PROFILE=0  # Set to 1 to enable profiling
export MLX_VERBOSE=0  # Set to 1 for verbose output

# RAM-specific optimizations (will be set during installation)
# Default optimizations - will be replaced during setup
export MLX_BATCH_SIZE=32
export MLX_MAX_SEQUENCE_LENGTH=8192

# Function to show current MLX status
mlx-env-status() {
    echo "🔥 MLX Environment Status:"
    echo "   Cache Dir: $MLX_CACHE_DIR"
    echo "   Models Dir: $MLX_MODELS_DIR"
    echo "   Threads: $OMP_NUM_THREADS"
    echo "   Cache Size: ${MLX_CACHE_SIZE_MB}MB"
    echo "   GPU Memory: $(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo 'Not Set')MB"
    echo "   HF Cache: $HF_HOME"
    echo "   Memory Pool: ${MLX_MEMORY_POOL:-Not Set}"
    echo "   Lazy Loading: ${MLX_LAZY_LOADING:-Not Set}"
}

# Function to reset MLX environment variables
mlx-env-reset() {
    echo "🔄 Resetting MLX environment variables..."
    unset MLX_MEMORY_POOL MLX_LAZY_LOADING MLX_CACHE_SIZE_MB
    unset OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS
    unset HF_HOME HF_HUB_CACHE TRANSFORMERS_CACHE
    unset MLX_CACHE_DIR MLX_MODELS_DIR
    unset MLX_BATCH_SIZE MLX_MAX_SEQUENCE_LENGTH
    unset MLX_PROFILE MLX_VERBOSE
    echo "✅ MLX environment variables reset"
}

# Backward compatibility alias
mlx_status() {
    mlx-env-status
}

# Function to monitor MLX performance
mlx_monitor() {
    echo "📊 MLX Performance Monitor"
    while true; do
        MEMORY_USAGE=$(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | grep -E "(python|mlx)" | head -5)
        GPU_MEMORY=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo "0")
        
        clear
        echo "🚀 MLX Performance Dashboard - $(date)"
        echo "================================"
        echo "GPU Memory Limit: ${GPU_MEMORY}MB"
        echo ""
        echo "Top MLX Processes:"
        echo "$MEMORY_USAGE"
        
        sleep 2
    done
}

echo "🔥 MLX advanced environment loaded for M4"
echo "💡 Run 'mlx_status' to see current configuration"
echo "📊 Run 'mlx_monitor' to monitor performance"
