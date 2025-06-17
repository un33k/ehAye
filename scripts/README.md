# ehAye-Local Scripts

This directory contains entry point scripts that provide direct access to CLI functionality.

## Entry Point Scripts

### Core CLI Scripts
- `benchmark` - Performance benchmarking for LLM models
- `chat` - Interactive chat interface with LLM models  
- `models` - Model download, installation, and management
- `system` - System diagnostics and management
- `ollama-launch` - Quick launcher for Ollama with specified models (standalone)

### Setup Scripts
- `setup-pyenv` - Create pyenv virtual environment for isolated Python version management

### Usage

Make sure you have installed the package first:
```bash
pip install -e .
```

Then you can run any script directly:
```bash
# Model management
./scripts/models list
./scripts/models download phi3

# Interactive chat
./scripts/chat

# Performance benchmarking  
./scripts/benchmark

# System information
./scripts/system info

# Ollama launcher (standalone - works without installation)
./scripts/ollama-launch list
./scripts/ollama-launch pull phi3
./scripts/ollama-launch run phi3

# Setup pyenv virtual environment (run once per project)
./scripts/setup-pyenv
```

### Python Environment Management

For projects requiring specific Python versions, use the pyenv setup script:

```bash
# Default setup (Python 3.11.9)
./scripts/setup-pyenv

# Custom Python version
PYTHON_VERSION=3.12.0 ./scripts/setup-pyenv

# Custom virtual environment name
VENV_NAME=my-custom-env ./scripts/setup-pyenv
```

### Other Scripts

- `development/` - Development tools (linting, formatting, testing)
- `deployment/` - Build and packaging scripts
- `setup/` - Installation and bootstrap scripts

All scripts are executable and include proper error handling and help messages.