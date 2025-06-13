#!/usr/bin/env bash
set -euo pipefail

# -------------------------------
# LLM Model Installation Script for MLX
# 
# Downloads and manages LLM models optimized for MLX on Apple Silicon
# -------------------------------

# Handle help flag early, before virtual environment check
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "help" ]]; then
    cat << EOF
📖 Usage: ./install-llm.sh [COMMAND] [OPTIONS]

Commands:
    setup               Setup model directories and download models
    list                List installed models
    search [PATTERN]    Search available models (e.g., mistral, llama, phi)
    download <MODEL>    Download a specific model by name
    cleanup             Clean up cached models
    help                Show this help message

Examples:
    ./install-llm.sh setup             # Initial setup and model download
    ./install-llm.sh list              # Show installed models
    ./install-llm.sh search mistral    # Search for Mistral models
    ./install-llm.sh download mistral-7b # Download Mistral 7B model
    ./install-llm.sh search            # List all available models
    ./install-llm.sh cleanup           # Clean up cache

💡 Note: Requires virtual environment activation first:
    source .venv/bin/activate && ./install-llm.sh setup
EOF
    return 0 2>/dev/null || exit 0
fi

echo "🤖 MLX Model Installation and Management"
echo "========================================"

# Check if we're in the correct virtual environment
CURRENT_PYTHON=$(which python)
EXPECTED_VENV_PYTHON="$(pwd)/.venv/bin/python"

if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
    echo "❌ Error: Not in a virtual environment!"
    echo "🔒 For safety, model downloads require a virtual environment."
    echo ""
    echo "💡 To fix this:"
    echo "   1. Run: source .venv/bin/activate"
    echo "   2. Or run: ./install-venv.sh"
    echo "   3. Then re-run this script"
    exit 1
fi

# Verify we're using the expected Python from our venv
if [[ "$CURRENT_PYTHON" != "$EXPECTED_VENV_PYTHON" ]]; then
    echo "❌ Error: Not using the correct virtual environment!"
    echo "🔍 Current Python: $CURRENT_PYTHON"
    echo "🎯 Expected Python: $EXPECTED_VENV_PYTHON"
    echo ""
    echo "💡 To fix this:"
    echo "   1. Run: source .venv/bin/activate"
    echo "   2. Verify with: which python"
    echo "   3. Then re-run this script"
    exit 1
fi

echo "✅ Correct virtual environment detected: $CURRENT_PYTHON"

# Get system memory for recommendations
MEM_TOTAL_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
echo "📊 System memory: ${MEM_TOTAL_GB}GB"

# --- Model Database ---
# Comprehensive list of available MLX models
get_model_info() {
    local key="$1"
    case "$key" in
        # Small Models (< 3B parameters)
        "phi-2") echo "mlx-community/phi-2:small:2.7B:Microsoft Phi-2 - Fast and capable" ;;
        "llama-3.2-1b") echo "mlx-community/Llama-3.2-1B-Instruct-4bit:small:1B:Meta Llama 3.2 1B - Ultra lightweight" ;;
        "llama-3.2-3b") echo "mlx-community/Llama-3.2-3B-Instruct-4bit:small:3B:Meta Llama 3.2 3B - Compact but capable" ;;
        "deepseek-coder-lite") echo "mlx-community/DeepSeek-Coder-V2-Lite-Instruct-4bit-mlx:small:2.46B:DeepSeek Coder V2 Lite - Latest code model" ;;
        "deepseek-1.3b") echo "mlx-community/deepseek-coder-1.3b-base-mlx:small:1.3B:DeepSeek Coder 1.3B - Base code model" ;;
        
        # Medium Models (3B-8B parameters)
        "qwen2.5-7b") echo "mlx-community/Qwen2.5-7B-Instruct-4bit:medium:7B:Qwen 2.5 7B - High quality instruction model" ;;
        "command-r-7b") echo "mlx-community/c4ai-command-r7b-12-2024-4bit:medium:7B:Command R 7B - Dec 2024 release" ;;
        "gemma-2-9b") echo "mlx-community/gemma-2-9b-it-4bit:medium:9B:Google Gemma 2 9B - Instruction tuned" ;;
        "mistral-small") echo "mlx-community/Mistral-Small-Instruct-2409-4bit:medium:7B:Mistral Small - Sept 2024" ;;
        "llama-3.2-11b-vision") echo "mlx-community/Llama-3.2-11B-Vision-Instruct-4bit:medium:11B:Meta Llama 3.2 11B - Vision capable" ;;
        
        # Large Models (> 8B parameters)
        "qwen2.5-32b") echo "mlx-community/Qwen2.5-32B-Instruct-4bit:large:32B:Qwen 2.5 32B - High performance" ;;
        "qwen2.5-72b") echo "mlx-community/Qwen2.5-72B-Instruct-4bit:large:72B:Qwen 2.5 72B - Largest Qwen model" ;;
        "command-r-plus") echo "mlx-community/c4ai-command-r-plus-08-2024-4bit:large:35B:Command R Plus - Aug 2024" ;;
        "deepseek-r1") echo "mlx-community/DeepSeek-R1-3bit:large:67B:DeepSeek R1 - Latest reasoning model" ;;
        *) echo "" ;;
    esac
}

# Get all model keys
get_all_model_keys() {
    echo "phi-2 llama-3.2-1b llama-3.2-3b deepseek-coder-lite deepseek-1.3b qwen2.5-7b command-r-7b gemma-2-9b mistral-small llama-3.2-11b-vision qwen2.5-32b qwen2.5-72b command-r-plus deepseek-r1"
}

# --- Model Search Function ---
search_models() {
    local search_pattern="${1:-}"
    
    echo "🔍 Available MLX Models"
    echo "======================"
    
    if [[ -n "$search_pattern" ]]; then
        echo "🔎 Searching for: '$search_pattern'"
        echo ""
    fi
    
    # Function to get category emoji
    get_category_emoji() {
        case "$1" in
            "small") echo "🟢" ;;
            "medium") echo "🟡" ;;
            "large") echo "🔴" ;;
            "code") echo "💻" ;;
            *) echo "📦" ;;
        esac
    }
    
    # Function to format size for sorting
    size_sort_key() {
        local size="$1"
        if [[ "$size" =~ ^([0-9.]+)B$ ]]; then
            echo "${BASH_REMATCH[1]}" | awk '{printf "%05.1f", $1}'
        else
            echo "00000"
        fi
    }
    
    # Search and display models
    local found_models=()
    local search_lower=$(echo "$search_pattern" | tr '[:upper:]' '[:lower:]')
    
    for model_key in $(get_all_model_keys); do
        local model_info=$(get_model_info "$model_key")
        [[ -z "$model_info" ]] && continue
        
        IFS=':' read -r model_id category size description <<< "$model_info"
        
        # Check if pattern matches model key, ID, or description
        if [[ -z "$search_pattern" ]] || \
           [[ "$model_key" == *"$search_lower"* ]] || \
           [[ "$(echo "$model_id" | tr '[:upper:]' '[:lower:]')" == *"$search_lower"* ]] || \
           [[ "$(echo "$description" | tr '[:upper:]' '[:lower:]')" == *"$search_lower"* ]]; then
            
            # Create sortable entry: category|size_key|model_key|info
            local size_key=$(size_sort_key "$size")
            found_models+=("$category|$size_key|$model_key|$model_info")
        fi
    done
    
    if [[ ${#found_models[@]} -eq 0 ]]; then
        echo "❌ No models found matching '$search_pattern'"
        echo ""
        echo "💡 Try searching for:"
        echo "   • Model families: mistral, llama, phi, gemma"
        echo "   • Use cases: code, chat, instruct"
        echo "   • Sizes: 7b, 13b, 34b"
        echo "   • Companies: microsoft, meta, google"
        return 1
    fi
    
    # Sort models by category, then by size
    IFS=$'\n' found_models=($(sort -t'|' -k1,1 -k2,2n <<< "${found_models[*]}"))
    
    # Display models grouped by category
    local current_category=""
    local count=0
    
    for model_entry in "${found_models[@]}"; do
        IFS='|' read -r cat size_key model_key model_info <<< "$model_entry"
        IFS=':' read -r model_id category size description <<< "$model_info"
        
        # Print category header
        if [[ "$category" != "$current_category" ]]; then
            [[ -n "$current_category" ]] && echo ""
            local emoji=$(get_category_emoji "$category")
            case "$category" in
                "small") echo "$emoji Small Models (< 3B parameters):" ;;
                "medium") echo "$emoji Medium Models (3B-8B parameters):" ;;
                "large") echo "$emoji Large Models (> 8B parameters):" ;;
                "code") echo "$emoji Code Models (specialized for programming):" ;;
            esac
            current_category="$category"
        fi
        
        # Print model info
        count=$((count + 1))
        printf "  %2d. %-20s %s %-6s %s\n" "$count" "$model_key" "$(get_category_emoji "$category")" "($size)" "$description"
    done
    
    echo ""
    echo "📊 Found ${#found_models[@]} model(s)"
    
    if [[ -n "$search_pattern" ]]; then
        echo ""
        echo "💡 To download a model:"
        echo "   ./install-llm.sh download <model-key>"
        echo "   Example: ./install-llm.sh download mistral-7b"
    fi
}

# --- Download Specific Model ---
download_model_by_key() {
    local model_key="${1:-}"
    
    if [[ -z "$model_key" ]]; then
        echo "❌ Error: Model name is required"
        echo "💡 Usage: ./install-llm.sh download <model-key>"
        echo ""
        echo "🔍 To find available models:"
        echo "   ./install-llm.sh search"
        echo "   ./install-llm.sh search mistral"
        return 1
    fi
    
    # Set up cache directories
    export HF_HOME="$HOME/.mlx-cache/huggingface"
    export MLX_CACHE_DIR="$HOME/.mlx-cache/mlx"
    export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
    
    # Create directories if they don't exist
    mkdir -p "$MLX_MODELS_DIR"/{small,medium,large,code}
    mkdir -p "$HF_HOME"
    mkdir -p "$MLX_CACHE_DIR"
    mkdir -p "$HOME/.mlx-cache/transformers"
    
    # Get model info
    local model_info=$(get_model_info "$model_key")
    
    if [[ -z "$model_info" ]]; then
        echo "❌ Error: Model '$model_key' not found"
        echo ""
        echo "🔍 Available models:"
        echo "   ./install-llm.sh search"
        echo ""
        echo "💡 Popular models:"
        echo "   mistral-7b, phi-2, codellama-7b, llama-2-7b"
        return 1
    fi
    
    IFS=':' read -r model_id category size description <<< "$model_info"
    
    echo "📥 Downloading Model"
    echo "==================="
    echo "🏷️  Name: $model_key"
    echo "📦 Model ID: $model_id"
    echo "🏷️  Category: $category"
    echo "📊 Size: $size parameters"
    echo "📝 Description: $description"
    echo ""
    
    # Check if model is already downloaded
    if [[ -f "$MLX_MODELS_DIR/$category/.model_list" ]] && grep -q "$model_id" "$MLX_MODELS_DIR/$category/.model_list"; then
        echo "✅ Model '$model_key' is already downloaded"
        echo "📁 Location: $MLX_MODELS_DIR/$category/"
        return 0
    fi
    
    # Confirm download
    echo "🎯 Ready to download $description"
    read -p "Continue? (Y/n): " -r confirm
    if [[ $confirm =~ ^[Nn]$ ]]; then
        echo "❌ Download cancelled"
        return 1
    fi
    
    # Create download script
    cat > /tmp/download_model.py << EOF
import os
import sys
from mlx_lm import load
from huggingface_hub import snapshot_download

try:
    print("🔄 Starting download...")
    model, tokenizer = load('$model_id')
    print("✅ $description downloaded successfully")
    print(f"📁 Cached in: {os.environ.get('HF_HOME', 'default cache')}")
except Exception as e:
    print(f"❌ Download failed: {e}")
    sys.exit(1)
EOF
    
    # Download the model
    if python /tmp/download_model.py; then
        echo "✅ Model '$model_key' downloaded successfully"
        
        # Add to model list
        mkdir -p "$MLX_MODELS_DIR/$category"
        echo "model_id:$model_id" >> "$MLX_MODELS_DIR/$category/.model_list"
        
        echo ""
        echo "🎉 Download completed!"
        echo "💡 To use this model:"
        echo "   python chat.py --model $model_id"
        echo "   python benchmark.py --model $model_id"
    else
        echo "❌ Failed to download '$model_key'"
        rm -f /tmp/download_model.py
        return 1
    fi
    
    rm -f /tmp/download_model.py
}

# --- Smart Model Management ---
setup_models() {
    echo "🤖 Setting up intelligent model management..."
    
    # Create organized model directory structure in user home
    export HF_HOME="$HOME/.mlx-cache/huggingface"
    export MLX_CACHE_DIR="$HOME/.mlx-cache/mlx"
    export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
    
    mkdir -p "$MLX_MODELS_DIR"/{small,medium,large,code}
    mkdir -p "$HF_HOME"
    mkdir -p "$MLX_CACHE_DIR"
    mkdir -p "$HOME/.mlx-cache/transformers"
    
    echo "📂 Model directory structure created in ~/.mlx-cache/:"
    echo "   models/small/  - Models under 3B params"
    echo "   models/medium/ - Models 3B-8B params"
    echo "   models/large/  - Models over 8B params"
    echo "   models/code/   - Code-specialized models"
    echo "   huggingface/   - Hugging Face model cache"
    echo "   mlx/           - MLX-specific cache"
    echo "   transformers/  - Transformers library cache"
    
    # Recommend models based on available RAM
    echo ""
    echo "🎯 Recommended models for your ${MEM_TOTAL_GB}GB system:"
    
    if [[ $MEM_TOTAL_GB -lt 16 ]]; then
        RECOMMENDED_MODELS=(
            "mlx-community/phi-2-MLX:small:Phi-2 (2.7B) - Excellent for testing"
            "mlx-community/TinyLlama-1.1B-Chat-v1.0-4bit-mlx:small:TinyLlama (1.1B) - Ultra lightweight"
        )
    elif [[ $MEM_TOTAL_GB -lt 32 ]]; then
        RECOMMENDED_MODELS=(
            "mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx:medium:Mistral 7B (Recommended)"
            "mlx-community/CodeLlama-7b-Instruct-hf-4bit-mlx:code:CodeLlama 7B"
            "mlx-community/phi-2-MLX:small:Phi-2 (2.7B) - Fast testing"
        )
    else
        RECOMMENDED_MODELS=(
            "mlx-community/Mixtral-8x7B-Instruct-v0.1-4bit-mlx:large:Mixtral 8x7B - Best quality"
            "mlx-community/Llama-2-13b-chat-hf-4bit-mlx:large:Llama 2 13B"
            "mlx-community/Mistral-7B-Instruct-v0.1-4bit-mlx:medium:Mistral 7B (Recommended)"
            "mlx-community/CodeLlama-13b-Instruct-hf-4bit-mlx:code:CodeLlama 13B"
        )
    fi
    
    echo ""
    echo "📋 Available models:"
    for i in "${!RECOMMENDED_MODELS[@]}"; do
        IFS=':' read -r model_id category description <<< "${RECOMMENDED_MODELS[$i]}"
        echo "$((i+1)). $description"
    done
    echo "$((${#RECOMMENDED_MODELS[@]}+1)). Download multiple models"
    echo "$((${#RECOMMENDED_MODELS[@]}+2)). Skip model download"
    
    echo ""
    read -p "Select option (1-$((${#RECOMMENDED_MODELS[@]}+2))): " -r selection
    
    download_model() {
        local model_id="$1"
        local category="$2"
        local description="$3"
        
        echo "📥 Downloading $description..."
        echo "   Model: $model_id"
        echo "   Category: $category"
        
        # Create download script for better error handling
        cat > /tmp/download_model.py << EOF
import os
import sys
from mlx_lm import load
from huggingface_hub import snapshot_download

try:
    print("🔄 Starting download...")
    model, tokenizer = load('$model_id')
    print("✅ $description downloaded successfully")
    print(f"📁 Cached in: {os.environ.get('HF_HOME', 'default cache')}")
except Exception as e:
    print(f"❌ Download failed: {e}")
    sys.exit(1)
EOF
        
        if python /tmp/download_model.py; then
            echo "✅ $description ready for use"
            mkdir -p "$MLX_MODELS_DIR/$category"
            echo "model_id:$model_id" >> "$MLX_MODELS_DIR/$category/.model_list"
        else
            echo "❌ Failed to download $description"
        fi
        
        rm -f /tmp/download_model.py
    }
    
    if [[ $selection -eq $((${#RECOMMENDED_MODELS[@]}+1)) ]]; then
        echo "📥 Downloading multiple recommended models..."
        for model_info in "${RECOMMENDED_MODELS[@]}"; do
            IFS=':' read -r model_id category description <<< "$model_info"
            download_model "$model_id" "$category" "$description"
        done
    elif [[ $selection -eq $((${#RECOMMENDED_MODELS[@]}+2)) ]]; then
        echo "⏭️  Skipping model download"
    elif [[ $selection -ge 1 && $selection -le ${#RECOMMENDED_MODELS[@]} ]]; then
        model_info="${RECOMMENDED_MODELS[$((selection-1))]}"
        IFS=':' read -r model_id category description <<< "$model_info"
        download_model "$model_id" "$category" "$description"
    else
        echo "❌ Invalid selection"
        exit 1
    fi
    
    # Create model list file
    echo "📝 Creating model registry..."
    cat > "$MLX_MODELS_DIR/model_registry.json" << EOF
{
    "last_updated": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "system_ram_gb": $MEM_TOTAL_GB,
    "cache_dir": "$MLX_CACHE_DIR",
    "models_dir": "$MLX_MODELS_DIR",
    "hf_cache": "$HF_HOME",
    "categories": {
        "small": "Models under 3B parameters",
        "medium": "Models 3B-8B parameters", 
        "large": "Models over 8B parameters",
        "code": "Code-specialized models"
    }
}
EOF
}

# --- Model Management Functions ---
list_models() {
    echo "📚 Installed Models:"
    echo "==================="
    
    # Set up cache directories
    export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
    export MLX_CACHE_DIR="$HOME/.mlx-cache"
    
    if [[ ! -d "$MLX_MODELS_DIR" ]]; then
        echo "❌ No models directory found at ~/.mlx-cache/models"
        echo "   Run: ./install-llm.sh setup"
        exit 1
    fi
    
    for category in small medium large code; do
        if [[ -f "$MLX_MODELS_DIR/$category/.model_list" ]]; then
            echo ""
            echo "📂 $category models:"
            while IFS=':' read -r model_id; do
                model_name=$(basename "$model_id")
                echo "   • $model_name"
            done < "$MLX_MODELS_DIR/$category/.model_list"
        fi
    done
    
    # Show cache size
    if [[ -d "$MLX_CACHE_DIR" ]]; then
        cache_size=$(du -sh "$MLX_CACHE_DIR" 2>/dev/null | cut -f1 || echo "0")
        echo ""
        echo "💾 Total cache size (~/.mlx-cache): $cache_size"
        
        # Show breakdown
        for subdir in huggingface mlx models transformers; do
            if [[ -d "$MLX_CACHE_DIR/$subdir" ]]; then
                subdir_size=$(du -sh "$MLX_CACHE_DIR/$subdir" 2>/dev/null | cut -f1 || echo "0")
                echo "   $subdir: $subdir_size"
            fi
        done
    fi
}

cleanup_models() {
    echo "🗑️  Model Cleanup"
    echo "================="
    
    # Set up cache directories
    export MLX_CACHE_DIR="$HOME/.mlx-cache"
    export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
    
    if [[ ! -d "$MLX_CACHE_DIR" ]]; then
        echo "❌ No cache directory found at ~/.mlx-cache"
        exit 1
    fi
    
    cache_size=$(du -sh "$MLX_CACHE_DIR" 2>/dev/null | cut -f1 || echo "0")
    echo "📊 Current cache size (~/.mlx-cache): $cache_size"
    
    echo ""
    echo "Select cleanup option:"
    echo "1. Clear all cached models"
    echo "2. Clear specific model category"
    echo "3. Cancel"
    
    read -p "Choose option (1-3): " -r cleanup_option
    
    case $cleanup_option in
        1)
            read -p "⚠️  Clear ALL cached models and data in ~/.mlx-cache? (y/N): " -r confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                rm -rf "$MLX_CACHE_DIR"/*
                echo "✅ All cached models and data cleared from ~/.mlx-cache"
            else
                echo "❌ Cleanup cancelled"
            fi
            ;;
        2)
            echo "Select category to clear:"
            echo "1. Small models"
            echo "2. Medium models" 
            echo "3. Large models"
            echo "4. Code models"
            echo "5. Hugging Face cache"
            echo "6. MLX cache"
            echo "7. Transformers cache"
            read -p "Choose category (1-7): " -r cat_option
            
            case $cat_option in
                1) category="small" ;;
                2) category="medium" ;;
                3) category="large" ;;
                4) category="code" ;;
                5) 
                    read -p "⚠️  Clear Hugging Face cache? (y/N): " -r confirm
                    if [[ $confirm =~ ^[Yy]$ ]]; then
                        rm -rf "$MLX_CACHE_DIR/huggingface"/*
                        echo "✅ Hugging Face cache cleared"
                    fi
                    return 0
                    ;;
                6)
                    read -p "⚠️  Clear MLX cache? (y/N): " -r confirm
                    if [[ $confirm =~ ^[Yy]$ ]]; then
                        rm -rf "$MLX_CACHE_DIR/mlx"/*
                        echo "✅ MLX cache cleared"
                    fi
                    return 0
                    ;;
                7)
                    read -p "⚠️  Clear Transformers cache? (y/N): " -r confirm
                    if [[ $confirm =~ ^[Yy]$ ]]; then
                        rm -rf "$MLX_CACHE_DIR/transformers"/*
                        echo "✅ Transformers cache cleared"
                    fi
                    return 0
                    ;;
                *) echo "❌ Invalid selection"; exit 1 ;;
            esac
            
            if [[ -f "$MLX_MODELS_DIR/$category/.model_list" ]]; then
                rm -f "$MLX_MODELS_DIR/$category/.model_list"
                echo "✅ $category model list cleared"
            fi
            ;;
        3)
            echo "❌ Cleanup cancelled"
            ;;
        *)
            echo "❌ Invalid selection"
            exit 1
            ;;
    esac
}

# --- Show Help (redirect to early help) ---
show_help() {
    # This function exists for compatibility but help is shown earlier
    echo "Use: ./install-llm.sh --help for detailed help"
}

# Parse command line arguments
COMMAND="${1:-setup}"

case $COMMAND in
    setup)
        setup_models
        ;;
    list)
        list_models
        ;;
    search)
        search_models "${2:-}"
        ;;
    download)
        download_model_by_key "${2:-}"
        ;;
    cleanup)
        cleanup_models
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac

echo ""
echo "🎉 Model management completed!"
echo ""
echo "💡 Next steps:"
echo "   • Search models: ./install-llm.sh search [pattern]"
echo "   • List installed: ./install-llm.sh list"
echo "   • Start chatting: python chat.py"
echo "   • Run benchmarks: python benchmark.py"
echo "   • Run performance tests: python performance-test.py"
echo "   • Advanced management: python mlx-manager.py"