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
📖 Usage: ./llm.sh [COMMAND] [OPTIONS]

Commands:
    setup               Setup model directories and download models
    list                List installed models
    -l                  Short for list
    search [PATTERN]    Search available models (e.g., mistral, llama, phi)
    -s [PATTERN]        Short for search
    -f [FLAVOR]         Filter search results by flavor/keyword (use with -s)
    download <MODEL>    Download a specific model by name or number from search
    -d <MODEL|ID>       Short for download (use model key or number from search)
    install <MODEL_ID>  Auto-install model by full model ID (non-interactive)
    -i <MODEL_ID>       Short for install
    cleanup             Clean up cached models
    help                Show this help message

Examples:
    ./llm.sh setup             # Initial setup and model download
    ./llm.sh -l                # Show installed models
    ./llm.sh -s mistral        # Search for Mistral models
    ./llm.sh -s deepseek -f coder  # Search DeepSeek models filtered by 'coder'
    ./llm.sh -s llama -f 7B    # Search Llama models filtered by '7B'
    ./llm.sh -d mistral-7b     # Download Mistral 7B model
    ./llm.sh -d 2              # Download model #2 from last search
    ./llm.sh install mlx-community/Meta-Llama-3-8B-Instruct-4bit  # Auto-install
    ./llm.sh -i mlx-community/DeepSeek-R1-Distill-Qwen-1.5B-4bit   # Auto-install short
    ./llm.sh search            # List all available models
    ./llm.sh cleanup           # Clean up cache

💡 Note: Requires virtual environment activation first:
    source .venv/bin/activate && ./llm.sh setup
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
    echo "   2. Or run: ./venv.sh"
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

# --- Global Variables ---
# Store last search results for numbered downloads
LAST_SEARCH_RESULTS_FILE="/tmp/mlx_last_search_results.txt"

# --- Dynamic Model Search Functions ---
# Search Hugging Face for MLX models
search_huggingface_models() {
    local search_pattern="$1"
    local filter_flavor="$2"
    
    echo "🔍 Searching Hugging Face for MLX models..."
    
    # Create Python script to search Hugging Face Hub
    cat > /tmp/search_hf_models.py << 'EOF'
import requests
import json
import sys
import re
from urllib.parse import quote

def search_models(query, filter_flavor=None):
    # Search for models in mlx-community organization
    url = f"https://huggingface.co/api/models?search={quote(query)}&author=mlx-community&limit=100"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        models = response.json()
        
        results = []
        
        for model in models:
            model_id = model.get('id', '')
            model_name = model_id.split('/')[-1] if '/' in model_id else model_id
            
            # Skip if not from mlx-community
            if not model_id.startswith('mlx-community/'):
                continue
                
            # Apply flavor filter if specified
            if filter_flavor:
                if filter_flavor.lower() not in model_name.lower():
                    continue
            
            # Extract model info
            tags = model.get('tags', [])
            downloads = model.get('downloads', 0)
            
            # Extract size from model name and determine category
            size = "Unknown"
            category = "medium"  # default
            
            size_match = re.search(r'(\d+(?:\.\d+)?)[Bb]', model_name)
            if size_match:
                size_num = float(size_match.group(1))
                size = f"{size_match.group(1)}B"
                
                if size_num < 2:
                    category = "tiny"
                elif size_num < 8:
                    category = "small"
                elif size_num < 15:
                    category = "medium"
                else:
                    category = "large"
            else:
                # Skip models with unknown sizes
                continue
            
            # Only add models with known sizes
            if size != "Unknown":
                results.append({
                    'id': model_id,
                    'name': model_name,
                    'category': category,
                    'size': size,
                    'downloads': downloads,
                    'tags': tags
                })
        
        # Sort by downloads (popularity)
        results.sort(key=lambda x: x['downloads'], reverse=True)
        
        return results
        
    except Exception as e:
        print(f"Error searching models: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    flavor = sys.argv[2] if len(sys.argv) > 2 else None
    
    models = search_models(query, flavor)
    
    for model in models:
        print(f"{model['id']}:{model['category']}:{model['size']}:{model['name']} - {model['downloads']} downloads")
EOF
    
    # Run the search
    python /tmp/search_hf_models.py "$search_pattern" "$filter_flavor" 2>/dev/null
    local exit_code=$?
    
    # Clean up
    rm -f /tmp/search_hf_models.py
    
    return $exit_code
}

# Function to get category emoji
get_category_emoji() {
    case "$1" in
        "tiny") echo "🔵" ;;
        "small") echo "🟢" ;;
        "medium") echo "🟡" ;;
        "large") echo "🔴" ;;
        *) echo "📦" ;;
    esac
}

# --- Model Search Function ---
search_models() {
    local search_pattern="${1:-}"
    local filter_flavor="${2:-}"
    
    echo "🔍 Available MLX Models"
    echo "======================"
    
    if [[ -n "$search_pattern" ]]; then
        echo "🔎 Searching for: '$search_pattern'"
        if [[ -n "$filter_flavor" ]]; then
            echo "🎯 Filtered by: '$filter_flavor'"
        fi
        echo ""
    fi
    
    # Use dynamic search if search pattern is provided
    local found_models=()
    
    if [[ -n "$search_pattern" ]]; then
        # Get models from Hugging Face API
        local hf_results
        hf_results=$(search_huggingface_models "$search_pattern" "$filter_flavor")
        
        if [[ -z "$hf_results" ]]; then
            echo "❌ No models found matching '$search_pattern'"
            if [[ -n "$filter_flavor" ]]; then
                echo "    with flavor '$filter_flavor'"
            fi
            echo ""
            echo "💡 Try searching for:"
            echo "   • Model families: mistral, llama, phi, gemma, deepseek"
            echo "   • Use cases: code, coder, instruct, chat"
            echo "   • Sizes: 1b, 3b, 7b, 13b, 70b"
            echo "   • Companies: microsoft, meta, google, deepseek"
            echo ""
            echo "📖 Usage examples:"
            echo "   ./llm.sh -s deepseek -f coder"
            echo "   ./llm.sh -s llama -f 7B"
            return 1
        fi
        
        # Parse HF results into our format
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            # Skip lines that don't look like model results
            [[ "$line" == *"Searching Hugging Face"* ]] && continue
            [[ "$line" != *":"* ]] && continue
            IFS=':' read -r model_id category size description <<< "$line"
            
            # Function to format size for sorting
            size_sort_key() {
                local size="$1"
                if [[ "$size" =~ ^([0-9.]+)B$ ]]; then
                    echo "${BASH_REMATCH[1]}" | awk '{printf "%05.1f", $1}'
                else
                    echo "00000"
                fi
            }
            
            local size_key=$(size_sort_key "$size")
            local model_key=$(basename "$model_id")
            found_models+=("$category|$size_key|$model_key|$model_id:$category:$size:$description")
        done <<< "$hf_results"
    else
        echo "💡 Please specify a search pattern:"
        echo "   ./llm.sh -s <pattern> [-f <flavor>]"
        echo ""
        echo "📖 Examples:"
        echo "   ./llm.sh -s deepseek        # All DeepSeek models"
        echo "   ./llm.sh -s deepseek -f coder # DeepSeek models with 'coder'"
        echo "   ./llm.sh -s llama -f 7B     # Llama models with '7B'"
        echo "   ./llm.sh -s mistral         # All Mistral models"
        return 0
    fi
    
    if [[ ${#found_models[@]} -eq 0 ]]; then
        echo "❌ No models found matching '$search_pattern'"
        if [[ -n "$filter_flavor" ]]; then
            echo "    with flavor '$filter_flavor'"
        fi
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
                "tiny") echo "$emoji Tiny Models (< 2B parameters):" ;;
                "small") echo "$emoji Small Models (2B-8B parameters):" ;;
                "medium") echo "$emoji Medium Models (8B-15B parameters):" ;;
                "large") echo "$emoji Large Models (> 15B parameters):" ;;
            esac
            current_category="$category"
        fi
        
        # Print model info in requested format
        count=$((count + 1))
        local org_name=$(echo "$model_id" | cut -d'/' -f1)
        printf "  %2d. (%s) %s [%s]\n" "$count" "$size" "$model_key" "$org_name"
    done
    
    echo ""
    echo "📊 Found ${#found_models[@]} model(s)"
    
    # Save search results for numbered downloads
    > "$LAST_SEARCH_RESULTS_FILE"  # Clear file
    for model_entry in "${found_models[@]}"; do
        IFS='|' read -r cat size_key model_key model_info <<< "$model_entry"
        IFS=':' read -r model_id category size description <<< "$model_info"
        echo "$model_id" >> "$LAST_SEARCH_RESULTS_FILE"
    done
    
    if [[ -n "$search_pattern" ]]; then
        echo ""
        echo "💡 To download a model:"
        echo "   ./llm.sh -d <number>          # By number from search"
        echo "   ./llm.sh -d <model-id>        # By full model ID"
        echo "   Example: ./llm.sh -d 1        # Download first result"
        echo ""
        echo "🔍 Refine your search:"
        echo "   ./llm.sh -s $search_pattern -f <flavor>  # Add flavor filter"
    fi
}

# --- Auto Install Model (Non-interactive) ---
auto_install_model() {
    local model_id="${1:-}"
    
    if [[ -z "$model_id" ]]; then
        echo "❌ Error: Model ID is required for auto-install"
        echo "💡 Usage: ./llm.sh install <full-model-id>"
        echo "   Example: ./llm.sh install mlx-community/Meta-Llama-3-8B-Instruct-4bit"
        return 1
    fi
    
    # Validate model ID format
    if [[ "$model_id" != *"/"* ]]; then
        echo "❌ Error: Model ID must be in format 'organization/model-name'"
        echo "   Example: mlx-community/Meta-Llama-3-8B-Instruct-4bit"
        return 1
    fi
    
    # Set up cache directories
    export HF_HOME="$HOME/.mlx-cache/huggingface"
    export MLX_CACHE_DIR="$HOME/.mlx-cache/mlx"
    export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
    
    # Create directories if they don't exist
    mkdir -p "$MLX_MODELS_DIR"/{tiny,small,medium,large}
    mkdir -p "$HF_HOME"
    mkdir -p "$MLX_CACHE_DIR"
    mkdir -p "$HOME/.mlx-cache/transformers"
    
    # Extract model info from ID
    local model_name=$(basename "$model_id")
    local category="medium"  # default
    local size="Unknown"
    
    # Extract size and category from model name
    if [[ "$model_name" =~ [0-9]+(\.[0-9]+)?[Bb] ]]; then
        local size_match
        size_match=$(echo "$model_name" | grep -oE '[0-9]+(\.[0-9]+)?[Bb]' | head -1)
        local size_num=${size_match%[Bb]}
        size="${size_num}B"
        
        # Simple integer comparison
        if [[ "${size_num%.*}" -lt 2 ]]; then
            category="tiny"
        elif [[ "${size_num%.*}" -lt 8 ]]; then
            category="small"
        elif [[ "${size_num%.*}" -lt 15 ]]; then
            category="medium"
        else
            category="large"
        fi
    fi
    
    echo "📥 Auto-installing Model"
    echo "========================"
    echo "📦 Model ID: $model_id"
    echo "🏷️  Name: $model_name"
    echo "📊 Size: $size"
    echo "🏷️  Category: $category"
    echo ""
    
    # Check if model is already downloaded
    if [[ -f "$MLX_MODELS_DIR/$category/.model_list" ]] && grep -q "$model_id" "$MLX_MODELS_DIR/$category/.model_list"; then
        echo "✅ Model '$model_name' is already installed"
        echo "📁 Location: $MLX_MODELS_DIR/$category/"
        return 0
    fi
    
    # Create download script
    cat > /tmp/auto_install_model.py << EOF
import os
import sys
from mlx_lm import load

try:
    print("🔄 Downloading model...")
    model, tokenizer = load('$model_id')
    print("✅ Model downloaded successfully")
    print(f"📁 Cached in: {os.environ.get('HF_HOME', 'default cache')}")
except Exception as e:
    print(f"❌ Download failed: {e}")
    sys.exit(1)
EOF
    
    # Download the model
    if python /tmp/auto_install_model.py; then
        echo "✅ Model '$model_name' installed successfully"
        
        # Add to model list
        mkdir -p "$MLX_MODELS_DIR/$category"
        echo "model_id:$model_id" >> "$MLX_MODELS_DIR/$category/.model_list"
        
        echo ""
        echo "🎉 Auto-install completed!"
        echo "💡 To use this model:"
        echo "   python chat.py --model $model_id"
        echo "   python benchmark.py --model $model_id"
    else
        echo "❌ Failed to install '$model_name'"
        rm -f /tmp/auto_install_model.py
        return 1
    fi
    
    rm -f /tmp/auto_install_model.py
}

# --- Download Specific Model ---
download_model_by_key() {
    local model_input="${1:-}"
    local model_key="$model_input"
    
    if [[ -z "$model_input" ]]; then
        echo "❌ Error: Model name or number is required"
        echo "💡 Usage: ./llm.sh download <model-key>"
        echo "         ./llm.sh -d <model-key>"
        echo "         ./llm.sh -d <number>  # From search results"
        echo ""
        echo "🔍 To find available models:"
        echo "   ./llm.sh search"
        echo "   ./llm.sh -s mistral"
        return 1
    fi
    
    # Check if input is a number (referring to search results)
    if [[ "$model_input" =~ ^[0-9]+$ ]]; then
        if [[ ! -f "$LAST_SEARCH_RESULTS_FILE" ]]; then
            echo "❌ Error: No previous search results found"
            echo "💡 Run a search first: ./llm.sh -s <pattern>"
            return 1
        fi
        
        # Get model key from search results by line number
        model_key=$(sed -n "${model_input}p" "$LAST_SEARCH_RESULTS_FILE")
        
        if [[ -z "$model_key" ]]; then
            local total_results=$(wc -l < "$LAST_SEARCH_RESULTS_FILE" 2>/dev/null || echo "0")
            echo "❌ Error: Invalid model number '$model_input'"
            echo "💡 Available numbers: 1-$total_results"
            echo "   Run: ./llm.sh -s <pattern> to see models"
            return 1
        fi
        
        echo "🎯 Selected model #$model_input: $model_key"
    fi
    
    # Set up cache directories
    export HF_HOME="$HOME/.mlx-cache/huggingface"
    export MLX_CACHE_DIR="$HOME/.mlx-cache/mlx"
    export MLX_MODELS_DIR="$HOME/.mlx-cache/models"
    
    # Create directories if they don't exist
    mkdir -p "$MLX_MODELS_DIR"/{tiny,small,medium,large}
    mkdir -p "$HF_HOME"
    mkdir -p "$MLX_CACHE_DIR"
    mkdir -p "$HOME/.mlx-cache/transformers"
    
    # If model_key looks like a full model ID (contains '/'), use it directly
    local model_id="$model_key"
    local category="medium"  # default
    local size="Unknown"
    local description="$model_key"
    
    # If it's a full model ID, extract info from it
    if [[ "$model_key" == *"/"* ]]; then
        # Already a full model ID
        model_id="$model_key"
        local model_name=$(basename "$model_id")
        description="$model_name"
        
        # Extract size and category from model name
        if [[ "$model_name" =~ [0-9]+(\.?[0-9]*)?[Bb] ]]; then
            local size_match
            size_match=$(echo "$model_name" | grep -oE '[0-9]+(\.?[0-9]*)?[Bb]' | head -1)
            local size_num=${size_match%[Bb]}
            size="${size_num}B"
            
            # Simple integer comparison without bc dependency
            if [[ "${size_num%.*}" -lt 2 ]]; then
                category="tiny"
            elif [[ "${size_num%.*}" -lt 8 ]]; then
                category="small"
            elif [[ "${size_num%.*}" -lt 15 ]]; then
                category="medium"
            else
                category="large"
            fi
        fi
        
        # Category is determined by size only
    else
        echo "❌ Error: Model '$model_key' not found or invalid format"
        echo ""
        echo "🔍 To find models:"
        echo "   ./llm.sh -s <search-pattern>"
        echo "   ./llm.sh -s deepseek -f coder"
        echo ""
        echo "💡 Then download by number:"
        echo "   ./llm.sh -d <number>"
        return 1
    fi
    
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
    
    mkdir -p "$MLX_MODELS_DIR"/{tiny,small,medium,large}
    mkdir -p "$HF_HOME"
    mkdir -p "$MLX_CACHE_DIR"
    mkdir -p "$HOME/.mlx-cache/transformers"
    
    echo "📂 Model directory structure created in ~/.mlx-cache/:"
    echo "   models/tiny/   - Models under 2B params"
    echo "   models/small/  - Models 2B-8B params"
    echo "   models/medium/ - Models 8B-15B params"
    echo "   models/large/  - Models over 15B params"
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
        "tiny": "Models under 2B parameters",
        "small": "Models 2B-8B parameters",
        "medium": "Models 8B-15B parameters", 
        "large": "Models over 15B parameters"
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
        echo "   Run: ./llm.sh setup"
        exit 1
    fi
    
    local total_models=0
    local has_models=false
    
    for category in tiny small medium large; do
        if [[ -f "$MLX_MODELS_DIR/$category/.model_list" ]] && [[ -s "$MLX_MODELS_DIR/$category/.model_list" ]]; then
            has_models=true
            echo ""
            
            # Get category emoji and description
            local emoji=$(get_category_emoji "$category")
            case "$category" in
                "tiny") echo "$emoji Tiny Models (< 2B parameters):" ;;
                "small") echo "$emoji Small Models (2B-3B parameters):" ;;
                "medium") echo "$emoji Medium Models (3B-8B parameters):" ;;
                "large") echo "$emoji Large Models (> 8B parameters):" ;;
            esac
            
            local count=0
            while IFS=':' read -r prefix model_id; do
                if [[ "$prefix" == "model_id" ]]; then
                    count=$((count + 1))
                    total_models=$((total_models + 1))
                    
                    # Extract model name and make it more readable
                    model_name=$(basename "$model_id")
                    model_name=${model_name//-/ }  # Replace hyphens with spaces
                    model_name=${model_name//_/ }  # Replace underscores with spaces
                    
                    # Try to determine model size from ID
                    local size_info=""
                    if [[ "$model_id" =~ ([0-9]+[Bb]) ]]; then
                        size_info=" (${BASH_REMATCH[1]^^})"
                    elif [[ "$model_id" =~ ([0-9]+\.[0-9]+[Bb]) ]]; then
                        size_info=" (${BASH_REMATCH[1]^^})"
                    fi
                    
                    printf "   %2d. 🤖 %s%s\n" "$count" "$model_name" "$size_info"
                    printf "       📦 %s\n" "$model_id"
                fi
            done < "$MLX_MODELS_DIR/$category/.model_list"
        fi
    done
    
    if [[ "$has_models" == "false" ]]; then
        echo ""
        echo "📭 No models installed yet"
        echo "💡 To download models:"
        echo "   ./llm.sh -s <pattern>  # Search available models"
        echo "   ./llm.sh -d <number>   # Download by number"
        echo "   ./llm.sh setup         # Setup with recommended models"
    else
        echo ""
        echo "📊 Total installed models: $total_models"
    fi
    
    # Show cache size
    if [[ -d "$MLX_CACHE_DIR" ]]; then
        cache_size=$(du -sh "$MLX_CACHE_DIR" 2>/dev/null | cut -f1 || echo "0")
        echo ""
        echo "💾 Total cache size (~/.mlx-cache): $cache_size"
        
        # Show breakdown with emojis
        for subdir in huggingface mlx models transformers; do
            if [[ -d "$MLX_CACHE_DIR/$subdir" ]]; then
                subdir_size=$(du -sh "$MLX_CACHE_DIR/$subdir" 2>/dev/null | cut -f1 || echo "0")
                case "$subdir" in
                    "huggingface") echo "   🤗 $subdir: $subdir_size" ;;
                    "mlx") echo "   🔥 $subdir: $subdir_size" ;;
                    "models") echo "   📦 $subdir: $subdir_size" ;;
                    "transformers") echo "   🔄 $subdir: $subdir_size" ;;
                esac
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
            echo "1. Tiny models"
            echo "2. Small models"
            echo "3. Medium models" 
            echo "4. Large models"
            echo "5. Hugging Face cache"
            echo "6. MLX cache"
            echo "7. Transformers cache"
            read -p "Choose category (1-7): " -r cat_option
            
            case $cat_option in
                1) category="tiny" ;;
                2) category="small" ;;
                3) category="medium" ;;
                4) category="large" ;;
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
    echo "Use: ./llm.sh --help for detailed help"
}

# Parse command line arguments
COMMAND="${1:-setup}"
FLAVOR_FILTER=""

# Parse arguments for search with flavor
if [[ "$COMMAND" == "-s" || "$COMMAND" == "search" ]]; then
    SEARCH_PATTERN="${2:-}"
    # Check for -f flag
    if [[ "${3:-}" == "-f" && -n "${4:-}" ]]; then
        FLAVOR_FILTER="$4"
    fi
fi

case $COMMAND in
    setup)
        setup_models
        ;;
    list|-l)
        list_models
        ;;
    search|-s)
        search_models "$SEARCH_PATTERN" "$FLAVOR_FILTER"
        ;;
    download|-d)
        download_model_by_key "${2:-}"
        ;;
    install|-i)
        auto_install_model "${2:-}"
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
echo "   • Search models: ./llm.sh search [pattern]"
echo "   • List installed: ./llm.sh list"
echo "   • Start chatting: python chat.py"
echo "   • Run benchmarks: python benchmark.py"
echo "   • Run performance tests: python performance-test.py"
