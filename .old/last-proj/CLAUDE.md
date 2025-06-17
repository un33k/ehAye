# CLAUDE.md

This document provides guidance to Claude Code (claude.ai/code) for working with the ehAye repository.

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

## Project Structure
- `ali/` - Main package
  - `backends/` - Ollama & MLX backend implementations
  - `cli/` - Command-line interfaces (migrating from Typer to Click)
  - `core/` - Configuration, logging, exceptions
  - `llm/` - Chat and text generation logic
  - `models/` - Model management and registry
  - `benchmarks/` - Performance benchmarking tools
  - `system/` - System monitoring utilities
- `config/` - TOML configuration files
- `tests/` - Test suite (unit and integration)
- `scripts/` - Entry point scripts
- `web/` - Future web interface (placeholder)

## Important Files
- `pyproject.toml` - Project config & dependencies
- `config/settings.toml` - Runtime settings
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

### Current Status
- Migration from Typer to Click in progress
- API server and web interface planned
- Focus on stability and performance for v0.1.0 release