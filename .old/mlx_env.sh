#!/usr/bin/env bash
# MLX Environment Variables Setup
# Source this file to set up optimized MLX environment variables
# Uses centralized configuration from mlx-config.json

# Function to read JSON config and set environment variables
setup_mlx_env() {
    echo "🔧 Loading MLX configuration from mlx-config.json..."
    
    # Check if mlx-config.json exists
    if [[ ! -f "mlx-config.json" ]]; then
        echo "❌ Error: mlx-config.json not found"
        return 1
    fi
    
    # Use Python to read JSON and output export statements
    eval $(python3 -c "
import json
import os
from pathlib import Path

try:
    with open('mlx-config.json', 'r') as f:
        config = json.load(f)
    
    home_dir = str(Path.home())
    
    # Set environment variables
    for var, value in config['environment_variables'].items():
        expanded_value = value.replace('~', home_dir)
        print(f'export {var}=\"{expanded_value}\"')
    
    # Create directories
    for path_name, path_value in config['paths'].items():
        expanded_path = path_value.replace('~', home_dir)
        print(f'mkdir -p \"{expanded_path}\"')
    
    # Create model category directories
    models_dir = config['environment_variables']['MLX_MODELS_DIR'].replace('~', home_dir)
    for category in config['model_categories']:
        print(f'mkdir -p \"{models_dir}/{category}\"')
        
except Exception as e:
    print(f'echo \"❌ Error reading config: {e}\"', file=sys.stderr)
" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo "✅ MLX environment configured from mlx-config.json"
        echo ""
        echo "🔧 Environment Variables Set:"
        echo "   MLX_CACHE_DIR=$MLX_CACHE_DIR"
        echo "   MLX_MODELS_DIR=$MLX_MODELS_DIR"
        echo "   HF_HOME=$HF_HOME"
        echo "   OMP_NUM_THREADS=$OMP_NUM_THREADS"
        echo "   MLX_MEMORY_POOL=$MLX_MEMORY_POOL"
        echo "   TRANSFORMERS_CACHE=$TRANSFORMERS_CACHE"
        echo ""
        echo "✅ MLX environment ready for optimal performance!"
    else
        echo "❌ Failed to configure MLX environment"
        return 1
    fi
}

# Run the setup
setup_mlx_env