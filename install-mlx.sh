#!/usr/bin/env bash
set -euo pipefail

# -------------------------------
# MLX Setup Script for macOS
# 
# Installs and configures MLX (Machine Learning eXtended) for optimal 
# LLM performance on Apple Silicon Macs
# Note:
# This script is designed to be run as a one-time setup script.
# This script is designed to run on macOS and ARM64 architecture.
# -------------------------------

# Handle help flag early
if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
    cat << EOF
🔥 MLX Installation Script for macOS

Usage: ./install-mlx.sh [OPTIONS]

Description:
    Complete MLX setup for optimal LLM performance on Apple Silicon Macs.
    Configures system, installs dependencies, sets up Python environment,
    and optimizes GPU memory allocation.

Options:
    -h, --help    Show this help message and exit

Features:
    • System requirements check (RAM, disk, chip detection)
    • GPU memory optimization based on total RAM
    • Homebrew and build dependencies installation
    • Python virtual environment setup (via install-venv.sh)
    • MLX and machine learning packages installation
    • Performance optimization configuration
    • Model management setup (via install-llm.sh)
    • Usage scripts preparation

Prerequisites:
    • macOS (Apple Silicon recommended)
    • At least 8GB RAM (16GB+ recommended)
    • 50GB+ free disk space

Examples:
    ./install-mlx.sh         # Full MLX installation
    ./install-mlx.sh -h      # Show this help

Post-installation:
    1. Restart terminal (for GPU settings)
    2. Activate environment: source .venv/bin/activate
    3. Load optimizations: source mlx-env.sh
    4. Download models: ./install-llm.sh setup
    5. Start chatting: python chat.py
EOF
    exit 0
fi

echo "🚀 Setting up MLX for optimal LLM performance on macOS..."

# --- System Requirements Check ---
check_system() {
    echo "🔍 Checking system requirements..."
    
    # Check if running on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo "❌ Error: This script is designed for macOS only"
        exit 1
    fi
    
    # Get Apple Silicon chip info
    CHIP_INFO=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Apple Silicon")
    echo "🔥 Chip: $CHIP_INFO"
    
    # Get detailed system memory info
    MEM_TOTAL_GB=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    MEM_PRESSURE=$(memory_pressure | grep "System-wide memory free percentage" | awk '{print $5}' | tr -d '%' 2>/dev/null || echo "N/A")
    
    echo "📊 Total system memory: ${MEM_TOTAL_GB}GB"
    [[ "$MEM_PRESSURE" != "N/A" ]] && echo "💾 Current memory free: ${MEM_PRESSURE}%"
    
    # More nuanced memory warnings
    if [[ $MEM_TOTAL_GB -lt 8 ]]; then
        echo "❌ Error: Less than 8GB RAM. MLX requires at least 8GB for basic models."
        exit 1
    elif [[ $MEM_TOTAL_GB -lt 16 ]]; then
        echo "⚠️  Warning: Less than 16GB RAM. Only small models (Phi-2, small Mistral) recommended."
    elif [[ $MEM_TOTAL_GB -lt 32 ]]; then
        echo "✅ 16-32GB RAM: Good for 7B models and moderate quantization."
    else
        echo "🚀 ${MEM_TOTAL_GB}GB RAM: Excellent for large models and multiple concurrent sessions."
    fi
    
    # Check available disk space (macOS compatible)
    DISK_FREE=$(df -h . | tail -1 | awk '{print $4}')
    # Convert to GB for consistent reporting
    if [[ $DISK_FREE == *"T"* ]]; then
        DISK_FREE_GB=$(echo $DISK_FREE | sed 's/T$//' | awk '{printf "%.0f", $1 * 1024}')
    elif [[ $DISK_FREE == *"G"* ]]; then
        DISK_FREE_GB=$(echo $DISK_FREE | sed 's/G$//' | awk '{printf "%.0f", $1}')
    elif [[ $DISK_FREE == *"M"* ]]; then
        DISK_FREE_GB=$(echo $DISK_FREE | sed 's/M$//' | awk '{printf "%.1f", $1 / 1024}')
    else
        DISK_FREE_GB="0"
    fi
    echo "💽 Available disk space: ${DISK_FREE_GB}GB"
    
    if [[ $DISK_FREE_GB -lt 50 ]]; then
        echo "⚠️  Warning: Less than 50GB free space. Models require significant storage."
    fi
}

# --- GPU Memory Optimization ---
setup_gpu_memory() {
    echo "🎯 Configuring GPU memory allocation..."
    
    # Calculate optimal GPU memory allocation based on specified formula
    # m=RAM, r=reserve
    if [[ $MEM_TOTAL_GB -lt 24 ]]; then
        # No reservation for RAM < 24GB - maximize GPU usage
        RESERVE_GB=0
        echo "🔥 Low RAM detected: Allocating maximum memory to GPU"
    elif [[ $MEM_TOTAL_GB -eq 24 ]]; then
        # m=24, r=m-8
        RESERVE_GB=8
    elif [[ $MEM_TOTAL_GB -gt 24 && $MEM_TOTAL_GB -le 96 ]]; then
        # m >24 & m <=96, r=m-16
        RESERVE_GB=16
    elif [[ $MEM_TOTAL_GB -gt 96 && $MEM_TOTAL_GB -le 128 ]]; then
        # m >96 & m <=128, r=m-20
        RESERVE_GB=20
    elif [[ $MEM_TOTAL_GB -gt 128 && $MEM_TOTAL_GB -le 256 ]]; then
        # m >128 & m <=256, r=m-28
        RESERVE_GB=28
    else
        # m >256, r=m-30
        RESERVE_GB=30
    fi
    
    GPU_ALLOC_MB=$(( (MEM_TOTAL_GB - RESERVE_GB) * 1024 ))
    
    echo "💾 Allocating ${GPU_ALLOC_MB}MB to GPU (reserving ${RESERVE_GB}GB for system)"
    echo "📈 GPU allocation: $((GPU_ALLOC_MB / 1024))GB / ${MEM_TOTAL_GB}GB total ($(( GPU_ALLOC_MB * 100 / (MEM_TOTAL_GB * 1024) ))%)"
    
    # Check current GPU memory setting
    CURRENT_GPU_MB=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo "0")
    if [[ $CURRENT_GPU_MB -eq $GPU_ALLOC_MB ]]; then
        echo "✅ GPU memory already optimally configured"
        return
    fi
    
    # Set GPU memory limit with better error handling
    echo "🔧 Setting GPU memory limit..."
    if sudo sysctl iogpu.wired_limit_mb=$GPU_ALLOC_MB 2>/dev/null; then
        echo "✅ GPU memory allocation set successfully"
        
        # Verify the setting took effect
        NEW_GPU_MB=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null || echo "0")
        if [[ $NEW_GPU_MB -eq $GPU_ALLOC_MB ]]; then
            echo "✅ GPU memory setting verified"
        else
            echo "⚠️  Warning: GPU memory setting may not have taken effect properly"
        fi
    else
        echo "⚠️  Warning: Failed to set GPU memory allocation. This may impact performance."
        echo "   Try running: sudo sysctl iogpu.wired_limit_mb=$GPU_ALLOC_MB"
    fi
    
    # Make persistent across reboots with backup
    echo "📝 Making GPU memory setting persistent..."
    SYSCTL_CONF="/etc/sysctl.conf"
    
    # Remove any existing iogpu settings
    sudo sed -i.bak '/iogpu.wired_limit_mb/d' "$SYSCTL_CONF" 2>/dev/null || true
    
    # Add new setting
    if echo "iogpu.wired_limit_mb=$GPU_ALLOC_MB" | sudo tee -a "$SYSCTL_CONF" >/dev/null 2>&1; then
        echo "✅ GPU memory setting will persist across reboots"
    else
        echo "⚠️  Warning: Could not make GPU memory setting persistent"
    fi
}

# --- Install Dependencies ---
install_dependencies() {
    echo "📦 Installing system dependencies..."
    
    # Check for Homebrew and install if needed
    if ! command -v brew &> /dev/null; then
        echo "🍺 Homebrew not found. Using install-brew.sh..."
        if [[ -f "install-brew.sh" ]]; then
            if chmod +x install-brew.sh && ./install-brew.sh; then
                echo "✅ Homebrew setup completed via install-brew.sh"
            else
                echo "❌ install-brew.sh failed"
                echo "💡 Try running: ./install-brew.sh"
                exit 1
            fi
        else
            echo "❌ install-brew.sh not found"
            echo "💡 Installing Homebrew directly for Apple Silicon Mac..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            
            # Add Homebrew to PATH for this session
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        echo "✅ Homebrew already available"
    fi
    
    echo "🔄 Updating Homebrew..."
    brew update
    


    # Install required packages with better error handling
    echo "🔧 Installing build dependencies..."
    PACKAGES=("cmake" "ninja" "pkg-config" "git" "curl" "wget")
    
    for package in "${PACKAGES[@]}"; do
        if brew list "$package" &>/dev/null; then
            echo "✅ $package already installed"
        else
            echo "📦 Installing $package..."
            brew install "$package" || echo "⚠️  Warning: Failed to install $package"
        fi
    done
    
    # Install additional useful tools
    echo "🛠️  Installing additional tools..."
    OPTIONAL_TOOLS=("htop" "tree" "jq" "ripgrep")
    
    for tool in "${OPTIONAL_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            brew install "$tool" 2>/dev/null || echo "⚠️  Optional: $tool installation skipped"
        fi
    done
}

# --- Setup Python Environment ---
setup_python_venv() {
    echo "🐍 Setting up Python environment for MLX..."
    
    # Check if install-venv.sh exists and use it
    echo "📦 Using install-venv.sh for Python and virtual environment setup..."
    if chmod +x install-venv.sh && ./install-venv.sh 3.11 -y --d ./.venv; then
        echo "✅ Python environment setup completed via install-venv.sh"
    else
        echo "❌ install-env.sh failed, please try to run it manual"
    fi

    # Ensure virtual environment is activated
    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
    elif [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "⚠️  Warning: No virtual environment found. Creating one..."
    fi
    
    # Check if we're in the correct virtual environment before any pip operations
    CURRENT_PYTHON=$(which python)
    EXPECTED_VENV_PYTHON="$(pwd)/.venv/bin/python"
    
    if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
        echo "❌ Error: Not in a virtual environment!"
        echo "🔒 For safety, pip operations require a virtual environment."
        echo ""
        echo "💡 To fix this:"
        echo "   1. Run: source .venv/bin/activate"
        echo "   2. Or run: ./install-venv.sh"
        echo "   3. Then re-run this installer"
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
        echo "   3. Then re-run this installer"
        exit 1
    fi
    
    echo "✅ Correct virtual environment active: $CURRENT_PYTHON"
    
    # Upgrade pip and install build tools
    echo "⬆️  Upgrading pip and installing build tools..."
    pip install --upgrade pip setuptools wheel
}

# --- Install MLX ---
install_mlx() {
    echo "🔥 Installing MLX and related packages..."
    
    # Check if we're in the correct virtual environment
    CURRENT_PYTHON=$(which python)
    EXPECTED_VENV_PYTHON="$(pwd)/.venv/bin/python"
    
    if [[ -z "${VIRTUAL_ENV:-}" ]] && [[ -z "${CONDA_DEFAULT_ENV:-}" ]]; then
        echo "❌ Error: Not in a virtual environment!"
        echo "🔒 For safety, MLX installation requires a virtual environment."
        echo ""
        echo "💡 To fix this:"
        echo "   1. Run: source .venv/bin/activate"
        echo "   2. Or run: ./install-venv.sh"
        echo "   3. Then re-run this installer"
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
        echo "   3. Then re-run this installer"
        exit 1
    fi
    
    echo "✅ Correct virtual environment detected: $CURRENT_PYTHON"
    
    # Install MLX core packages
    pip install mlx mlx-lm
    
    # Install additional useful packages
    pip install transformers tokenizers huggingface-hub
    pip install numpy scipy matplotlib
    pip install jupyter ipywidgets
    
    # Install optional but useful packages
    pip install rich typer click
    pip install gradio streamlit
    
    echo "✅ MLX installation completed"
}

# --- Advanced Performance Optimizations ---
apply_performance_optimizations() {
    echo "⚡ Applying advanced performance optimizations..."
    
    # Get CPU info for optimization
    CPU_CORES=$(sysctl -n hw.ncpu)
    CPU_THREADS=$(sysctl -n hw.logicalcpu)
    CHIP_TYPE=$(sysctl -n machdep.cpu.brand_string | grep -o "M[0-9]" || echo "Unknown")
    
    echo "🔧 Optimizing for ${CPU_CORES}-core ${CHIP_TYPE} processor"
    
    # Configure the existing mlx-env.sh template
    if [[ -f "mlx-env.sh" ]]; then
        echo "📝 Configuring mlx-env.sh template..."
        
        # Calculate cache size (10% of RAM)
        CACHE_SIZE_MB=$((MEM_TOTAL_GB * 100))
        
        # Replace placeholders in the template
        sed -i.bak \
            -e "s/__CACHE_SIZE_MB__/$CACHE_SIZE_MB/g" \
            -e "s/__CPU_CORES__/$CPU_CORES/g" \
            -e "s/__CHIP_TYPE__/$CHIP_TYPE/g" \
            mlx-env.sh
        
        # Update RAM-specific optimizations based on system memory
        if [[ $MEM_TOTAL_GB -ge 64 ]]; then
            # High-memory system optimizations
            sed -i.bak \
                -e 's/export MLX_BATCH_SIZE=.*/export MLX_BATCH_SIZE=32/' \
                -e 's/export MLX_MAX_SEQUENCE_LENGTH=.*/export MLX_MAX_SEQUENCE_LENGTH=8192/' \
                mlx-env.sh
            echo "export MLX_PRELOAD_MODELS=1" >> mlx-env.sh
        elif [[ $MEM_TOTAL_GB -ge 32 ]]; then
            # Medium-memory system optimizations
            sed -i.bak \
                -e 's/export MLX_BATCH_SIZE=.*/export MLX_BATCH_SIZE=16/' \
                -e 's/export MLX_MAX_SEQUENCE_LENGTH=.*/export MLX_MAX_SEQUENCE_LENGTH=4096/' \
                mlx-env.sh
        else
            # Low-memory system optimizations (keep defaults)
            echo "export MLX_OFFLOAD_INACTIVE=1" >> mlx-env.sh
        fi
        
        # Remove backup file
        rm -f mlx-env.sh.bak
        
        echo "✅ mlx-env.sh configured successfully"
    else
        echo "❌ mlx-env.sh template not found"
    fi
    
    echo "✅ Performance optimization files ready:"
    echo "   📄 mlx-env.sh - Configured environment variables"
    echo "   🧪 performance-test.py - Performance test suite"
    echo "   💬 chat.py - Interactive chat interface"
    echo "   📊 benchmark.py - Model benchmarking tool"
    echo ""
    echo "💡 Usage:"
    echo "   source mlx-env.sh           # Load optimizations"
    echo "   python performance-test.py  # Test performance"
    echo "   python chat.py              # Start chatting"
    echo "   python benchmark.py         # Run benchmarks"
}

# --- Model Management ---
setup_models() {
    echo "🤖 Setting up model management..."
    
    # Check if install-llm.sh exists and use it
    if [[ -f "install-llm.sh" ]]; then
        echo "📦 Using install-llm.sh for model management..."
        if chmod +x install-llm.sh && ./install-llm.sh setup; then
            echo "✅ Model setup completed via install-llm.sh"
        else
            echo "❌ install-llm.sh failed"
            echo "💡 Try running: ./install-llm.sh setup"
        fi
    else
        echo "❌ install-llm.sh not found"
        echo "💡 Model management has been moved to install-llm.sh"
        echo "   Create that file or run model downloads manually"
    fi
}

# --- Prepare Usage Scripts ---
prepare_usage_scripts() {
    echo "📝 Preparing usage scripts..."
    
    # Verify all required scripts exist
    REQUIRED_SCRIPTS=("chat.py" "benchmark.py" "performance-test.py" "mlx-manager.py")
    MISSING_SCRIPTS=()
    
    for script in "${REQUIRED_SCRIPTS[@]}"; do
        if [[ ! -f "$script" ]]; then
            MISSING_SCRIPTS+=("$script")
        fi
    done
    
    if [[ ${#MISSING_SCRIPTS[@]} -gt 0 ]]; then
        echo "❌ Missing required scripts: ${MISSING_SCRIPTS[*]}"
        echo "   Please ensure all script files are in the current directory"
        return 1
    fi
    
    # Make sure all scripts are executable
    chmod +x chat.py benchmark.py performance-test.py mlx-manager.py
    
    echo "✅ All usage scripts are ready:"
    echo "   💬 chat.py - Interactive chat interface"
    echo "   📊 benchmark.py - Model benchmarking tool"
    echo "   🧪 performance-test.py - Performance test suite"
    echo "   🛠️  mlx-manager.py - Advanced model management"
}

# --- Main Installation Process ---
main() {
    echo "🍎 MLX Installation for macOS"
    echo "============================="
    
    check_system
    setup_gpu_memory
    install_dependencies
    setup_python_venv
    install_mlx
    apply_performance_optimizations
    setup_models
    prepare_usage_scripts
    
    echo ""
    echo "🎉 MLX setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Restart your terminal to apply GPU memory settings"
    echo "2. Activate environment: source .venv/bin/activate"
    echo "3. Load optimizations: source mlx-env.sh"
    echo "4. Download models: ./install-llm.sh setup"
    echo "5. Start chatting: python chat.py"
    echo "6. Run benchmark: python benchmark.py"
    echo ""
    echo "💡 Model management:"
    echo "   • Download models: ./install-llm.sh setup"
    echo "   • List models: ./install-llm.sh list"
    echo "   • Clean up: ./install-llm.sh cleanup"
    echo ""
    echo "🔥 Enjoy running LLMs with MLX!"
}

# Run main function
main "$@"
