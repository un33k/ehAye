#!/usr/bin/env bash
set -euo pipefail

# -------------------------------
# envy — Setup and activate virtualenv using pyenv
#
# Usage:
#   source ./envy                        # Uses default Python version, pyenv virtualenv
#   source ./envy 3.10.8                 # Uses specific Python version, pyenv virtualenv
#   source ./envy 3.10.8 -y              # Auto-accept closest match installation
#   source ./envy --d ./venv             # Uses local directory instead of pyenv virtualenv
#   source ./envy 3.10.8 --d ./venv -y   # All options combined
#   source ./envy --help                 # Show help
#
# Requirements:
#   - Homebrew (for pyenv installation if needed on macOS)
#   - pyenv (will be installed if missing)
# -------------------------------

# --- Config ---
DEFAULT_PYTHON_VERSION="3.11.9"
VENV_DIR=""
USE_LOCAL_VENV=false
AUTO_ACCEPT=false
SHOW_HELP=false

# --- Functions ---
show_help() {
    cat << EOF
Setup and activate virtualenv using pyenv

USAGE:
    source ./install-venv.sh [VERSION] [OPTIONS]

ARGUMENTS:
    VERSION     Python version to use (default: $DEFAULT_PYTHON_VERSION)

OPTIONS:
    --d DIR     Use local directory for virtualenv instead of pyenv virtualenv
    -y          Auto-accept closest match installation
    --help      Show this help message

EXAMPLES:
    source ./install-venv.sh                        # Default version, pyenv virtualenv
    source ./install-venv.sh 3.10.8                 # Specific version, pyenv virtualenv  
    source ./install-venv.sh --d ./venv             # Default version, local directory
    source ./install-venv.sh 3.10.8 --d ./venv -y   # All options combined

EOF
}

# Detect shell for better compatibility
detect_shell() {
    if [ -n "${ZSH_VERSION:-}" ]; then
        echo "zsh"
    elif [ -n "${BASH_VERSION:-}" ]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

SHELL_TYPE=$(detect_shell)

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --d)
            if [[ $# -lt 2 ]]; then
                echo "❌ Error: --d requires a directory argument"
                return 1 2>/dev/null || exit 1
            fi
            VENV_DIR="$2"
            USE_LOCAL_VENV=true
            shift 2
            ;;
        -y)
            AUTO_ACCEPT=true
            shift
            ;;
        -*)
            echo "❌ Error: Unknown option $1"
            echo "Use --help for usage information"
            return 1 2>/dev/null || exit 1
            ;;
        *)
            # Validate Python version format
            if [[ ! "$1" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
                echo "❌ Error: Invalid Python version format: $1"
                echo "Expected format: X.Y or X.Y.Z (e.g., 3.11 or 3.11.9)"
                return 1 2>/dev/null || exit 1
            fi
            PYTHON_VERSION="$1"
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    show_help
    return 0 2>/dev/null || exit 0
fi

# Set default version if none provided
PYTHON_VERSION="${PYTHON_VERSION:-$DEFAULT_PYTHON_VERSION}"

# --- Check and install pyenv if needed ---
install_pyenv() {
    echo "🔧 pyenv not found. Installing for macOS..."
    
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        return 1 2>/dev/null || exit 1
    fi
    
    # Install pyenv and pyenv-virtualenv
    brew install pyenv pyenv-virtualenv
    
    # Add to zsh config  
    SHELL_CONFIG="$HOME/.zshrc"
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$SHELL_CONFIG"
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> "$SHELL_CONFIG"
    echo 'eval "$(pyenv init -)"' >> "$SHELL_CONFIG"
    echo 'eval "$(pyenv virtualenv-init -)"' >> "$SHELL_CONFIG"
    
    # Initialize pyenv for current session
    export PYENV_ROOT="$HOME/.pyenv"
    command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    
    # Initialize pyenv-virtualenv
    if [ -d "$PYENV_ROOT/plugins/pyenv-virtualenv" ]; then
        eval "$(pyenv virtualenv-init -)"
    fi
}

# --- Setup pyenv ---
if ! command -v pyenv &> /dev/null; then
    install_pyenv
fi

# Initialize pyenv and pyenv-virtualenv for current session
export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Check for and initialize pyenv-virtualenv
PYENV_VIRTUALENV_AVAILABLE=false
if [ -d "$PYENV_ROOT/plugins/pyenv-virtualenv" ] || command -v pyenv-virtualenv &> /dev/null; then
    eval "$(pyenv virtualenv-init -)"
    PYENV_VIRTUALENV_AVAILABLE=true
else
    echo "⚠️  pyenv-virtualenv not found. Will use standard venv instead."
fi

# --- Smart Python version resolution ---
echo "🔍 Checking for Python $PYTHON_VERSION..."

# Get installed versions with error handling
echo "🔧 Attempting to get pyenv versions..."
if ! INSTALLED_VERSIONS=$(pyenv versions --bare 2>&1); then
    echo "❌ Error: Failed to get pyenv versions list"
    echo "   Error details: $INSTALLED_VERSIONS"
    echo "   Pyenv location: $(which pyenv 2>/dev/null || echo 'not found')"
    return 1 2>/dev/null || exit 1
fi

if [ -z "$INSTALLED_VERSIONS" ]; then
    echo "⚠️  No Python versions installed in pyenv yet"
    INSTALLED_VERSIONS=""
else
    echo "✅ Found $(echo "$INSTALLED_VERSIONS" | wc -l) installed Python versions"
fi

# Check for exact match first
echo "🔍 Looking for exact match: $PYTHON_VERSION"
if echo "$INSTALLED_VERSIONS" | grep -q "^$PYTHON_VERSION$"; then
    echo "✅ Found exact match: $PYTHON_VERSION"
    CLOSEST_VERSION="$PYTHON_VERSION"
else
    echo "🔍 No exact match, checking for compatible versions..."
    # Extract major.minor from requested version (e.g., 3.11 from 3.11 or 3.11.9)
    MAJOR_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f1-2)
    echo "🔍 Looking for ${MAJOR_MINOR}.x versions..."
    
    # Find locally installed versions that match major.minor
    LOCAL_MATCHES=$(echo "$INSTALLED_VERSIONS" | grep -E "^${MAJOR_MINOR}\.[0-9]+$" | sort -V || true)
    echo "🔍 Found local matches: '$LOCAL_MATCHES'"
    
    if [ -n "$LOCAL_MATCHES" ]; then
        echo "🔍 Python $PYTHON_VERSION not found locally. Checking for compatible versions..."
        # Found local compatible versions
        LATEST_LOCAL=$(echo "$LOCAL_MATCHES" | tail -1)
        echo "🎯 Found locally installed compatible version: $LATEST_LOCAL"
        
        if [ "$AUTO_ACCEPT" = false ]; then
            echo ""
            echo "💡 Options:"
            echo "   1. Use existing $LATEST_LOCAL (recommended - saves time)"
            echo "   2. Install exact version $PYTHON_VERSION"
            echo ""
            if [ "$SHELL_TYPE" = "zsh" ]; then
                read -q "?Use existing $LATEST_LOCAL? (Y/n) "
                USE_EXISTING=$?
                echo
            else
                read -p "Use existing $LATEST_LOCAL? (Y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Nn]$ ]]; then
                    USE_EXISTING=1
                else
                    USE_EXISTING=0
                fi
            fi
        else
            echo "🚀 Auto-accepting existing $LATEST_LOCAL"
            USE_EXISTING=0
        fi
        
        if [ $USE_EXISTING -eq 0 ]; then
            echo "✅ Using existing Python $LATEST_LOCAL"
            CLOSEST_VERSION="$LATEST_LOCAL"
        else
            echo "📦 Installing exact version $PYTHON_VERSION as requested..."
            CLOSEST_VERSION="$PYTHON_VERSION"
        fi
    else
        echo "🔍 Python $PYTHON_VERSION not found locally. No compatible ${MAJOR_MINOR}.x versions installed."
        echo "📦 Will proceed to install Python $PYTHON_VERSION"
        CLOSEST_VERSION="$PYTHON_VERSION"
    fi
fi

# Install version if not already present
echo "🔍 Debug: Checking if $CLOSEST_VERSION needs installation..."
echo "🔍 Debug: CLOSEST_VERSION=$CLOSEST_VERSION"
if ! echo "$INSTALLED_VERSIONS" | grep -q "^$CLOSEST_VERSION$"; then
    echo "📦 Installing Python $CLOSEST_VERSION..."
    
    # Get available versions for installation
    echo "🔍 Debug: Getting available versions for installation..."
    if ! AVAILABLE_VERSIONS=$(pyenv install --list 2>/dev/null | grep -E '^[[:space:]]*[0-9]+\.[0-9]+\.[0-9]+' | tr -d ' '); then
        echo "❌ Error: Failed to get available Python versions"
        return 1 2>/dev/null || exit 1
    fi
    echo "🔍 Debug: Found $(echo "$AVAILABLE_VERSIONS" | wc -l) available versions"
    
    # Check if exact version is available for installation
    echo "🔍 Debug: Checking if $CLOSEST_VERSION is available for installation..."
    if echo "$AVAILABLE_VERSIONS" | grep -q "^$CLOSEST_VERSION$"; then
        echo "✅ Found $CLOSEST_VERSION available for installation"
    else
        # Find closest available version
        INSTALLABLE_VERSION=$(echo "$AVAILABLE_VERSIONS" | grep -E "^${MAJOR_MINOR}\." | head -n 1)
        
        if [ -n "$INSTALLABLE_VERSION" ]; then
            echo "📦 Exact version not available. Closest: $INSTALLABLE_VERSION"
            if [ "$AUTO_ACCEPT" = false ]; then
                if [ "$SHELL_TYPE" = "zsh" ]; then
                    read -q "?Install $INSTALLABLE_VERSION instead? (y/N) "
                    RESPONSE=$?
                    echo
                    if [ $RESPONSE -ne 0 ]; then
                        echo "❌ Installation cancelled by user"
                        return 1 2>/dev/null || exit 1
                    fi
                else
                    read -p "Install $INSTALLABLE_VERSION instead? (y/N) " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        echo "❌ Installation cancelled by user"
                        return 1 2>/dev/null || exit 1
                    fi
                fi
            fi
            CLOSEST_VERSION="$INSTALLABLE_VERSION"
        else
            echo "❌ No compatible Python version found for $PYTHON_VERSION"
            echo "   Available ${MAJOR_MINOR}.x versions:"
            echo "$AVAILABLE_VERSIONS" | grep -E "^${MAJOR_MINOR}\." | head -5
            return 1 2>/dev/null || exit 1
        fi
    fi
    
    # Try to install using precompiled binary first
    echo "🚀 Attempting binary installation of Python $CLOSEST_VERSION..."
    
    # For macOS, try to use the faster binary installation
    if PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1 \
       PYTHON_BUILD_SKIP_MIRROR=1 \
       pyenv install --skip-existing "$CLOSEST_VERSION-macos" 2>/dev/null || \
       PYTHON_BUILD_MIRROR_URL_SKIP_CHECKSUM=1 \
       pyenv install --skip-existing "$CLOSEST_VERSION+macos" 2>/dev/null; then
        echo "✅ Binary installation successful!"
        # Update CLOSEST_VERSION to match what was actually installed
        CLOSEST_VERSION=$(pyenv versions --bare | grep "^$CLOSEST_VERSION" | head -1)
    else
        echo "⚠️  Binary not available for $CLOSEST_VERSION, checking for closest binary..."
        
        # Look for available binary versions for this major.minor
        BINARY_VERSIONS=$(pyenv install --list | grep -E "^[[:space:]]*${MAJOR_MINOR}\.[0-9]+.*macos" | tr -d ' ' | sort -V || true)
        
        if [ -n "$BINARY_VERSIONS" ]; then
            CLOSEST_BINARY=$(echo "$BINARY_VERSIONS" | tail -1)
            echo "📦 Found binary version: $CLOSEST_BINARY"
            
            if [ "$AUTO_ACCEPT" = false ]; then
                if [ "$SHELL_TYPE" = "zsh" ]; then
                    read -q "?Use binary $CLOSEST_BINARY instead? (Y/n) "
                    RESPONSE=$?
                    echo
                    if [ $RESPONSE -eq 0 ]; then
                        USE_BINARY=true
                    else
                        USE_BINARY=false
                    fi
                else
                    read -p "Use binary $CLOSEST_BINARY instead? (Y/n) " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Nn]$ ]]; then
                        USE_BINARY=false
                    else
                        USE_BINARY=true
                    fi
                fi
            else
                echo "🚀 Auto-accepting binary $CLOSEST_BINARY"
                USE_BINARY=true
            fi
            
            if [ "$USE_BINARY" = true ]; then
                echo "📦 Installing binary $CLOSEST_BINARY..."
                if pyenv install --skip-existing "$CLOSEST_BINARY"; then
                    echo "✅ Binary installation successful!"
                    # Extract the actual version number (remove -macos suffix)
                    CLOSEST_VERSION=$(echo "$CLOSEST_BINARY" | sed 's/-macos$//' | sed 's/+macos$//')
                else
                    echo "❌ Binary installation failed, falling back to source..."
                    USE_BINARY=false
                fi
            fi
        else
            echo "⚠️  No binary versions available for ${MAJOR_MINOR}.x"
            
            # Look for any available source versions as final option
            SOURCE_VERSIONS=$(echo "$AVAILABLE_VERSIONS" | grep -E "^${MAJOR_MINOR}\." | sort -V || true)
            if [ -n "$SOURCE_VERSIONS" ]; then
                BEST_SOURCE=$(echo "$SOURCE_VERSIONS" | tail -1)
                echo "📦 Best available source version: $BEST_SOURCE"
                
                if [ "$AUTO_ACCEPT" = false ]; then
                    if [ "$SHELL_TYPE" = "zsh" ]; then
                        read -q "?Install $BEST_SOURCE from source? (y/N) "
                        RESPONSE=$?
                        echo
                        if [ $RESPONSE -eq 0 ]; then
                            CLOSEST_VERSION="$BEST_SOURCE"
                            USE_BINARY=false
                        else
                            echo "❌ Installation cancelled by user"
                            return 1 2>/dev/null || exit 1
                        fi
                    else
                        read -p "Install $BEST_SOURCE from source? (y/N) " -n 1 -r
                        echo
                        if [[ $REPLY =~ ^[Yy]$ ]]; then
                            CLOSEST_VERSION="$BEST_SOURCE"
                            USE_BINARY=false
                        else
                            echo "❌ Installation cancelled by user"
                            return 1 2>/dev/null || exit 1
                        fi
                    fi
                else
                    echo "🚀 Auto-accepting source $BEST_SOURCE"
                    CLOSEST_VERSION="$BEST_SOURCE"
                    USE_BINARY=false
                fi
            else
                echo "❌ No compatible versions found for ${MAJOR_MINOR}.x"
                return 1 2>/dev/null || exit 1
            fi
        fi
        
        # Fall back to source compilation if no binary used
        if [ "${USE_BINARY:-false}" = false ]; then
            echo "⚠️  Using source compilation..."
            echo "   This may take several minutes to compile..."
            if ! pyenv install --skip-existing "$CLOSEST_VERSION"; then
                echo "❌ Error: Failed to install Python $CLOSEST_VERSION"
                return 1 2>/dev/null || exit 1
            fi
            echo "✅ Source compilation completed!"
        fi
    fi
else
    echo "🔍 Debug: $CLOSEST_VERSION already installed, skipping installation"
fi

echo "🐍 Selected Python version: $CLOSEST_VERSION"

# --- Create and activate virtualenv ---
if [ "$USE_LOCAL_VENV" = true ]; then
    # Use local directory
    if [ ! -d "$VENV_DIR" ]; then
        echo "📦 Creating virtual environment in $VENV_DIR..."
        "$PYENV_ROOT/versions/$CLOSEST_VERSION/bin/python" -m venv "$VENV_DIR"
    else
        echo "♻️ Virtual environment already exists: $VENV_DIR"
    fi
    
    # Activate the local virtualenv
    source "$VENV_DIR/bin/activate"
    echo "🚀 Activated local virtual environment ($VENV_DIR) using Python $CLOSEST_VERSION"
else
    # Use pyenv virtualenv (default behavior) or fallback to standard venv
    PROJECT_NAME=$(basename "$(pwd)")
    VENV_NAME="${PROJECT_NAME}-${CLOSEST_VERSION}"
    
    if [ "$PYENV_VIRTUALENV_AVAILABLE" = true ]; then
        # Try using pyenv virtualenv
        echo "🔄 Attempting to use pyenv virtualenv..."
        
        # Check if pyenv virtualenv already exists
        if pyenv versions --bare | grep -q "^$VENV_NAME$"; then
            echo "♻️ pyenv virtualenv already exists: $VENV_NAME"
        else
            echo "📦 Creating pyenv virtualenv: $VENV_NAME"
            if ! pyenv virtualenv "$CLOSEST_VERSION" "$VENV_NAME"; then
                echo "❌ Failed to create pyenv virtualenv. Falling back to standard venv."
                PYENV_VIRTUALENV_AVAILABLE=false
            fi
        fi
        
        # Try to activate pyenv virtualenv
        if [ "$PYENV_VIRTUALENV_AVAILABLE" = true ]; then
            if pyenv activate "$VENV_NAME" 2>/dev/null; then
                echo "🚀 Activated pyenv virtualenv ($VENV_NAME) using Python $CLOSEST_VERSION"
                # Set local Python version for this directory
                echo "$VENV_NAME" > .python-version
                echo "📌 Set local Python version to: $VENV_NAME"
            else
                echo "❌ Failed to activate pyenv virtualenv. Falling back to standard venv."
                PYENV_VIRTUALENV_AVAILABLE=false
            fi
        fi
    fi
    
    # Fallback to standard venv if pyenv-virtualenv failed or unavailable
    if [ "$PYENV_VIRTUALENV_AVAILABLE" = false ]; then
        echo "🔄 Using standard venv as fallback..."
        FALLBACK_VENV_DIR=".venv"
        
        if [ ! -d "$FALLBACK_VENV_DIR" ]; then
            echo "📦 Creating standard virtual environment in $FALLBACK_VENV_DIR..."
            "$PYENV_ROOT/versions/$CLOSEST_VERSION/bin/python" -m venv "$FALLBACK_VENV_DIR"
        else
            echo "♻️ Standard virtual environment already exists: $FALLBACK_VENV_DIR"
        fi
        
        # Activate the standard virtualenv
        source "$FALLBACK_VENV_DIR/bin/activate"
        echo "🚀 Activated standard virtual environment ($FALLBACK_VENV_DIR) using Python $CLOSEST_VERSION"
    fi
fi 