# CLAUDE.md

This document provides guidance to Claude Code (claude.ai/code) for working with the `ehAye` repository. The project name is called `ehAye` and should be reflected throughout the code and docs.

## Project Overview

**ehAye** is a professional-grade local LLM interface optimized for Apple Silicon Macs.

- **Purpose**: Unified interface for running LLMs locally with dual backend support
- **Language**: Python 3.10+
- **Version**: 0.1.0 (Alpha)
- **Main Command**: `ali` (Artificial Line Interface)
- **Dual Backends**:
  - **Ollama**: Easy model management, bypasses rate limits
  - **MLX**: Apple Silicon optimized inference (M1/M2/M3/M4)

## Description

ehAye provides a modular, extensible platform for local LLM deployment and interaction on macOS. The project focuses on:

### Core Features
- **Dual Backend Architecture**: Seamlessly switch between Ollama and MLX backends
- **Model Management**: Search, download, list, and remove models with curated categories
- **Interactive Chat**: Terminal-based chat with streaming responses
- **Performance Benchmarking**: Compare model performance across backends
- **Rich CLI**: Beautiful terminal output with color support and progress bars

### Current Capabilities
- Model categories: tiny (<2B), small (2B-3B), medium (3B-8B), large (>8B), code
- Ollama passthrough commands: `ali olla -- <command>`
- System monitoring: `ali sys info`
- Configuration via TOML files
- Comprehensive error handling and logging

### Planned Features
- Web interface for model interaction
- API server for programmatic access
- Enhanced pipeline development tools
- Integration with vector databases
- Advanced ETL capabilities with LlamaIndex/LangChain
- Deployment automation

## Key Commands

### Development
```bash
# Install/Update
pip install -e .

# Testing
pytest                    # Run all tests
pytest tests/unit/       # Unit tests only

# Code Quality
ruff check ali/          # Lint
black ali/               # Format
mypy ali/                # Type check
```

### CLI Usage
```bash
# Model Management
ali mod list             # List available models
ali mod search <query>   # Search for models
ali mod download <model> # Download a model
ali mod remove <model>   # Remove a model

# Chat & Generation
ali chat                 # Interactive chat (alias: ali chat interactive)
ali generate <prompt>    # Single generation

# Performance & System
ali perf benchmark       # Run performance benchmarks
ali sys info            # Show system information

# Backend Operations
ali olla -- <command>    # Passthrough to Ollama CLI
ali mlx <command>        # MLX-specific operations (planned)
```

## Project Structure (NEW MODULAR ARCHITECTURE)
- `ali/` - Main package
  - `backends/` - Backend implementations with enhanced modularity
    - `ollama/` - Ollama backend (client.py, service.py, models.py)
    - `mlx/` - MLX backend (engine.py, models.py, optimizer.py)
    - `base.py` - Backend interface definitions
    - `manager.py` - Backend management and switching
    - `utils.py` - Backend utilities and detection
  - `cli/` - Command-line interfaces (Click-based architecture)
    - `commands/` - Individual command implementations
    - `formatters/` - Rich output formatting (colors, tables, progress)
    - `main.py` - Main CLI entry point
  - `configuration/` - Enhanced configuration management
    - `manager.py` - Configuration loading and validation
    - `loader.py` - Configuration file handling
    - `paths.py` - Path management utilities
    - `environment.py` - Environment validation and setup
  - `logging/` - Advanced logging system
    - `logger.py` - Enhanced logger with rich output
    - `handlers.py` - Custom logging handlers
    - `formatters.py` - Multiple logging formatters (JSON, colored, etc.)
  - `exceptions/` - Categorized exception handling
    - `base.py` - Base exception classes
    - `backend_errors.py` - Backend-specific exceptions
    - `model_errors.py` - Model management exceptions
    - `cli_errors.py` - CLI-specific exceptions
  - `utilities/` - Shared utility modules
    - `console.py` - Rich console management
    - `system_info.py` - System information gathering
    - `validators.py` - Input validation utilities
    - `file_operations.py` - Safe file operations
    - `decorators.py` - Common decorators (retry, cache, etc.)
    - `async_helpers.py` - Async utilities
  - `chat/` - Enhanced chat system
    - `interface.py` - Chat interface management
    - `session.py` - Chat session handling
    - `history.py` - Conversation history
    - `streaming.py` - Streaming response handling
  - `generation/` - Text generation engine
    - `engine.py` - Generation orchestration
    - `parameters.py` - Generation parameter management
    - `processors.py` - Response processing
  - `models/` - Model management system
    - `registry.py` - Model registry and metadata
    - `downloader.py` - Model download handling
    - `installer.py` - Model installation logic
    - `categorizer.py` - Model categorization
    - `validator.py` - Model validation
  - `benchmarking/` - Performance analysis
    - `runner.py` - Benchmark execution
    - `metrics.py` - Performance metrics
    - `reporter.py` - Result reporting
    - `analyzers.py` - Performance analysis
    - `comparisons.py` - Backend comparisons
- `config/` - TOML configuration files
  - `app.toml` - Application settings
  - `backends.toml` - Backend configurations
  - `environment.toml` - Environment settings
  - `models.toml` - Model registry
- `scripts/` - Organized automation scripts
  - `setup/` - Installation and setup scripts
  - `development/` - Development workflow scripts
  - `deployment/` - Deployment automation
- `tests/` - Comprehensive test suite
  - `unit/` - Unit tests organized by module
  - `integration/` - Integration and workflow tests
  - `fixtures/` - Test data and fixtures
- `docs/` - Documentation system
  - `api/` - API reference documentation
  - `examples/` - Usage examples
- `web/` - Future web interface
  - `api/` - REST API server
  - `frontend/` - Web frontend
  - `static/` - Static assets

## Important Files
- `pyproject.toml` - Project config & dependencies
- `bootstrap.sh` - Complete setup automation
- `config/app.toml` - Application settings
- `config/backends.toml` - Backend configurations
- `config/models.toml` - Model registry

## Development Guidelines

### Code Standards
- Modules kept under 200 lines for maintainability
- Type hints throughout (mypy strict mode)
- Rich terminal output with color support
- Comprehensive error handling with custom exceptions
- Pre-commit hooks configured (black, ruff, mypy)

### Key Principles
- **User Experience First**: Minimal logging by default, clean output
- **Modular Design**: Easy to extend with new backends or features
- **Apple Silicon Optimization**: Leverage MLX for best performance
- **Professional Quality**: Production-ready code with tests

### New Architecture Benefits
- **Enhanced Modularity**: Clear separation of concerns across specialized modules
- **Better Error Handling**: Categorized exceptions with rich context and suggestions
- **Advanced Logging**: Multiple formatters, handlers, and performance monitoring
- **Rich Utilities**: Console management, validators, decorators, async helpers
- **Improved Testing**: Organized test structure with comprehensive fixtures
- **Professional Organization**: Industry-standard patterns and practices

### Current Status
- ✅ New modular architecture implemented
- ✅ Enhanced backend system with Ollama and MLX specialization
- ✅ Advanced configuration and logging systems
- ⏳ CLI migration to new structure in progress
- 🔄 Integration and testing phase
- 🎯 Focus on stability and performance for v0.1.0 release

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.