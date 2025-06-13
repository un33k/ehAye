#!/usr/bin/env bash
set -euo pipefail

# -------------------------------
# Homebrew Installation Script for macOS
# 
# Installs Homebrew package manager if not present
# -------------------------------

echo "🍺 Homebrew Installation Script"

# --- Check if Homebrew is already installed ---
check_homebrew() {
    if command -v brew &> /dev/null; then
        echo "✅ Homebrew already installed"
        BREW_VERSION=$(brew --version | head -1)
        echo "   Version: $BREW_VERSION"
        return 0
    else
        echo "📦 Homebrew not found, installing..."
        return 1
    fi
}

# --- Install Homebrew ---
install_homebrew() {
    echo "🔄 Installing Homebrew for Apple Silicon Mac..."
    
    # Download and install Homebrew
    if /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        echo "✅ Homebrew installed successfully"
    else
        echo "❌ Homebrew installation failed"
        exit 1
    fi
    
    # Add Homebrew to PATH for this session (Apple Silicon)
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        echo "🔧 Adding Homebrew to PATH..."
        eval "$(/opt/homebrew/bin/brew shellenv)"
        
        # Add to shell profile if not already there
        SHELL_CONFIG="$HOME/.zshrc"
        
        if [[ -f "$SHELL_CONFIG" ]]; then
            if ! grep -q "/opt/homebrew/bin/brew shellenv" "$SHELL_CONFIG"; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$SHELL_CONFIG"
                echo "📝 Added Homebrew to $SHELL_CONFIG"
            fi
        fi
    else
        echo "❌ Homebrew installation path not found"
        exit 1
    fi
}

# --- Update Homebrew ---
update_homebrew() {
    echo "🔄 Updating Homebrew..."
    if brew update; then
        echo "✅ Homebrew updated successfully"
    else
        echo "⚠️  Warning: Homebrew update failed, continuing anyway..."
    fi
}

# --- Verify Installation ---
verify_installation() {
    echo "🧪 Verifying Homebrew installation..."
    
    if command -v brew &> /dev/null; then
        BREW_VERSION=$(brew --version | head -1)
        echo "✅ Homebrew verification successful"
        echo "   Version: $BREW_VERSION"
        echo "   Location: $(which brew)"
        
        # Test basic functionality
        if brew --prefix &> /dev/null; then
            echo "   Prefix: $(brew --prefix)"
            echo "✅ Homebrew is fully functional"
            return 0
        else
            echo "⚠️  Warning: Homebrew prefix command failed"
            return 1
        fi
    else
        echo "❌ Homebrew verification failed"
        return 1
    fi
}

# --- Show Usage Information ---
show_usage() {
    echo ""
    echo "📋 Homebrew Installation Complete!"
    echo ""
    echo "💡 Next steps:"
    echo "   • Restart your terminal or run: source ~/.zshrc"
    echo "   • Verify installation: brew --version"
    echo "   • Install packages: brew install <package>"
    echo ""
    echo "🔗 Useful commands:"
    echo "   brew search <term>     - Search for packages"
    echo "   brew install <package> - Install a package"
    echo "   brew list              - List installed packages"
    echo "   brew update            - Update Homebrew"
    echo "   brew upgrade           - Upgrade installed packages"
}

# --- Show Help ---
show_help() {
    cat << EOF
🍺 Homebrew Installation Script

Usage: ./install-brew.sh [OPTIONS]

Description:
    Installs and configures Homebrew package manager for macOS.
    Automatically detects Apple Silicon and configures PATH correctly.

Options:
    -h, --help    Show this help message and exit

Features:
    • Checks if Homebrew is already installed
    • Downloads and installs Homebrew if needed  
    • Configures shell environment (adds to ~/.zshrc)
    • Updates Homebrew to latest version
    • Verifies installation is working

Examples:
    ./install-brew.sh         # Install/update Homebrew
    ./install-brew.sh -h      # Show this help

After installation:
    • Restart terminal or run: source ~/.zshrc
    • Verify with: brew --version
EOF
}

# --- Main Installation Process ---
main() {
    # Handle help flag
    if [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        show_help
        exit 0
    fi
    
    echo "🍎 Homebrew Setup for macOS"
    echo "============================"
    
    if check_homebrew; then
        update_homebrew
    else
        install_homebrew
        update_homebrew
    fi
    
    if verify_installation; then
        show_usage
        echo "🎉 Homebrew setup completed successfully!"
        exit 0
    else
        echo "❌ Homebrew setup encountered issues"
        echo "💡 Try running the script again or install manually:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
}

# Run main function
main "$@"