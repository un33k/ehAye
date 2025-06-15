#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# ehAye Local Bootstrap Script
# 
# Minimal bootstrap that only installs Homebrew and pyenv
# All other setup is handled by the Python-based system
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VERSION="${PYTHON_VERSION:-3.11.9}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This bootstrap script is designed for macOS"
        log_info "For other platforms, install Python 3.10+ and continue with:"
        log_info "  python -m venv .venv"
        log_info "  source .venv/bin/activate"
        log_info "  pip install -e ."
        exit 1
    fi
}

# Install Homebrew if not present
install_homebrew() {
    log_info "Checking for Homebrew..."
    
    if command -v brew >/dev/null 2>&1; then
        log_success "Homebrew already installed"
        return 0
    fi
    
    log_info "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    log_success "Homebrew installed"
}

# Install pyenv if not present
install_pyenv() {
    log_info "Checking for pyenv..."
    
    if command -v pyenv >/dev/null 2>&1; then
        log_success "pyenv already installed"
        return 0
    fi
    
    log_info "Installing pyenv..."
    brew install pyenv
    
    # Add pyenv to shell configuration
    {
        echo ''
        echo '# pyenv configuration'
        echo 'export PYENV_ROOT="$HOME/.pyenv"'
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"'
        echo 'eval "$(pyenv init -)"'
    } >> ~/.zprofile
    
    # Source for current session
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    
    log_success "pyenv installed"
}

# Install and set Python version
setup_python() {
    log_info "Setting up Python $PYTHON_VERSION..."
    
    # Check if version is already installed
    if pyenv versions --bare | grep -q "^$PYTHON_VERSION$"; then
        log_success "Python $PYTHON_VERSION already installed"
    else
        log_info "Installing Python $PYTHON_VERSION..."
        
        # Install with --skip-existing flag to avoid the prompt
        if ! pyenv install --skip-existing "$PYTHON_VERSION"; then
            log_error "Failed to install Python $PYTHON_VERSION"
            log_info "You can:"
            log_info "  1. Try a different Python version: PYTHON_VERSION=3.11.8 ./bootstrap.sh"
            log_info "  2. Install manually: pyenv install $PYTHON_VERSION"
            log_info "  3. Use system Python if compatible (3.10+)"
            exit 1
        fi
    fi
    
    # Set local Python version
    pyenv local "$PYTHON_VERSION"
    log_success "Python $PYTHON_VERSION set as local version"
}

# Create virtual environment
setup_venv() {
    log_info "Setting up virtual environment..."
    
    if [[ -d ".venv" ]]; then
        log_info "Virtual environment already exists"
    else
        log_info "Creating virtual environment..."
        python -m venv .venv
    fi
    
    log_success "Virtual environment ready"
}

# Install ehAye Local in development mode
install_ehaye() {
    log_info "Installing ehAye Local..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install in development mode
    pip install -e .
    
    log_success "ehAye Local installed in development mode"
}

# Run initial system setup
initial_setup() {
    log_info "Running initial system setup..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Run system setup
    python -m ehaye.cli.system_cli setup
    
    log_success "Initial setup completed"
}

# Main bootstrap function
main() {
    echo "🚀 ehAye Local Bootstrap"
    echo "======================="
    echo ""
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Platform check
    check_macos
    
    # Install dependencies
    install_homebrew
    install_pyenv
    
    # Setup Python environment
    setup_python
    setup_venv
    
    # Install ehAye Local
    install_ehaye
    
    # Initial setup
    initial_setup
    
    echo ""
    echo "🎉 Bootstrap completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Activate the environment: source .venv/bin/activate"
    echo "  2. Download models: ehaye-models search"
    echo "  3. Start chatting: ehaye-chat interactive"
    echo "  4. Run benchmarks: ehaye-benchmark validate"
    echo ""
    echo "Available commands:"
    echo "  • ehaye-chat       - Interactive chat interface"
    echo "  • ehaye-models     - Model management"
    echo "  • ehaye-benchmark  - Performance benchmarking"
    echo "  • ehaye-system     - System management"
    echo ""
    echo "Or use the script shortcuts:"
    echo "  • ./scripts/chat"
    echo "  • ./scripts/models"
    echo "  • ./scripts/benchmark"
    echo "  • ./scripts/system"
}

# Handle interruption
trap 'log_warning "Bootstrap interrupted"; exit 1' INT

# Run main function
main "$@"