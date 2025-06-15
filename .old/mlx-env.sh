#!/usr/bin/env bash
# MLX Environment Variables Setup
# Source this file to set up optimized MLX environment variables

# MLX Cache and Model Directories (in user home for persistence)
export MLX_CACHE_DIR="$HOME/.mlx-cache/mlx"
export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
export HF_HOME="$HOME/.mlx-cache/huggingface"

# OpenMP thread optimization for Apple Silicon
# Set to number of performance cores (adjust based on your system)
export OMP_NUM_THREADS=8

# MLX Memory Pool optimization for Apple Silicon
# Enable memory pooling for better performance
export MLX_MEMORY_POOL=1

# Additional MLX optimizations
export TRANSFORMERS_CACHE="$HOME/.mlx-cache/transformers"

# Create directories if they don't exist
mkdir -p "$MLX_CACHE_DIR"
mkdir -p "$MLX_MODELS_DIR"/{tiny,small,medium,large,code}
mkdir -p "$HF_HOME"
mkdir -p "$TRANSFORMERS_CACHE"

echo "🔧 MLX Environment Variables Set:"
echo "   MLX_CACHE_DIR=$MLX_CACHE_DIR"
echo "   MLX_MODELS_DIR=$MLX_MODELS_DIR"
echo "   HF_HOME=$HF_HOME"
echo "   OMP_NUM_THREADS=$OMP_NUM_THREADS"
echo "   MLX_MEMORY_POOL=$MLX_MEMORY_POOL"
echo "   TRANSFORMERS_CACHE=$TRANSFORMERS_CACHE"
echo ""
echo "✅ MLX environment ready for optimal performance!"