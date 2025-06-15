# ehAye Local

A modular, professional-grade LLM interface with dual backend support: Ollama for easy model access and MLX for Apple Silicon optimization.

## 🚀 Quick Start

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10 or higher

### Installation

1. **Bootstrap the environment (installs Python, MLX, and Ollama):**
   ```bash
   ./bootstrap.sh
   ```

2. **Activate the environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Download a model:**
   ```bash
   # Via Ollama (no rate limits!)
   ehaye-models search --backend ollama     # or: ehaye-models s -b ollama
   ehaye-models download phi3 --backend ollama
   
   # Via MLX (Apple Silicon optimized)  
   ehaye-models search --backend mlx        # or: ehaye-models s -b mlx
   ehaye-models download phi2 --backend mlx
   
   # Quick Ollama method
   ./scripts/ollama-launch pull phi3
   ```

4. **Start chatting:**
   ```bash
   ehaye-chat interactive
   ```

## ⚡ Quick CLI Usage

### Dual Backend Support
```bash
# Ollama backend (no rate limits, easy downloads)
ehaye-models s -b ollama              # Search Ollama models
ehaye-models d phi3 -b ollama         # Download via Ollama
ehaye-models l -b ollama              # List Ollama models

# MLX backend (Apple Silicon optimized)
ehaye-models s -b mlx                 # Search MLX models  
ehaye-models d phi2 -b mlx            # Download via MLX
ehaye-models l -b mlx                 # List MLX models

# Default backend (Ollama)
ehaye-models s                        # Uses default backend
ehaye-models d phi3                   # Downloads via Ollama
```

### Quick Ollama Scripts
```bash
./scripts/ollama-launch pull phi3     # Download model
./scripts/ollama-launch run phi3      # Interactive chat
./scripts/ollama-launch list          # List models
./scripts/ollama-launch start         # Start service
```

## 🏗️ Architecture

ehAye Local follows a clean, modular architecture with dual backend support:

```
src/
├── core/           # Configuration, environment, logging, exceptions
├── backends/       # Backend implementations (Ollama, MLX)
├── models/         # Model management (download, categorization, registry)
├── llm/           # LLM operations (chat, generation, prompts, streaming)
├── benchmarks/    # Performance testing and reporting
├── system/        # System monitoring and macOS integration
└── cli/           # Command-line interfaces
```

### Key Principles
- **Dual Backend Design**: Ollama for easy access, MLX for optimization
- **Modular Design**: Each module is self-contained and under 200 lines
- **Configuration-Driven**: TOML-based configuration system
- **Professional Standards**: Type hints, error handling, logging, tests
- **Rate Limit Avoidance**: Ollama bypasses Hugging Face restrictions

### Backend Strategy
- **Ollama Path**: Easy install, download, run, and test LLMs directly
- **MLX Path**: Use Ollama for downloads, MLX for optimized inference
- **Unified Interface**: Same CLI commands work with both backends

## 📦 Available Commands

### Chat Interface
```bash
ehaye-chat interactive              # Interactive chat session
ehaye-chat single "Your question"   # Single prompt
ehaye-chat models                   # List available models
```

### Model Management
```bash
# Backend-specific commands
ehaye-models list --backend ollama         # List Ollama models
ehaye-models search --backend mlx          # Search MLX models  
ehaye-models download phi3 --backend ollama # Download via Ollama
ehaye-models remove phi2 --backend mlx     # Remove MLX model
ehaye-models info phi3 --backend ollama    # Show Ollama model info

# Short aliases with backends
ehaye-models l -b ollama            # List Ollama models
ehaye-models s -b mlx              # Search MLX models
ehaye-models d phi3 -b ollama      # Download via Ollama
ehaye-models r phi2 -b mlx         # Remove MLX model
ehaye-models i phi3 -b ollama      # Info for Ollama model

# Default backend (Ollama)
ehaye-models list                   # Uses default backend
ehaye-models search [query]         # Search default backend
ehaye-models download <model-id>    # Download via default
```

### Quick Ollama Operations
```bash
./scripts/ollama-launch pull phi3   # Download model directly
./scripts/ollama-launch run phi3    # Start interactive chat
./scripts/ollama-launch list        # List all models
./scripts/ollama-launch start       # Start Ollama service
```

### Performance Benchmarking
```bash
ehaye-benchmark single -m <model>   # Benchmark single model
ehaye-benchmark compare --all       # Compare all models
ehaye-benchmark validate            # Check environment
```

### System Management
```bash
ehaye-system info                   # System information
ehaye-system validate              # Environment validation
ehaye-system config                 # Show configuration
ehaye-system setup                  # Initialize system
```

## ⚙️ Configuration

### Main Configuration (`config/settings.toml`)
```toml
[paths]
cache_dir = "~/.cache/ehaye"
models_dir = "~/.cache/ehaye/models"

[models]
default_backend = "ollama"    # "ollama" or "mlx"
backends = ["ollama", "mlx"]  # Available backends
categories = ["tiny", "small", "medium", "large", "code"]

[performance]
omp_num_threads = 8
mlx_memory_pool = true
max_cache_size_gb = 50

[chat]
default_temperature = 0.7
default_max_tokens = 512
streaming_enabled = true
```

### Model Configuration (`config/models.toml`)
Curated model lists organized by categories (tiny, small, medium, large, code) with aliases for easy access.

### Environment Configuration (`config/environment.toml`)
System-specific settings, environment variables, and validation parameters.

## 🔧 Development

### Project Structure
```
ehAye-Local/
├── src/ehaye/              # Main source code
├── scripts/                # Entry point scripts
├── config/                 # Configuration files
├── tests/                  # Test suite
├── web/                    # Future web interface
├── bootstrap.sh            # Setup script
└── pyproject.toml          # Modern Python project config
```

### Running Tests
```bash
pytest                      # Run all tests
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest -v --cov=src        # With coverage
```

### Code Quality
```bash
ruff check src/             # Linting
black src/                  # Code formatting
mypy src/                   # Type checking
```

## 🎯 Model Categories

- **🔵 Tiny** (< 2B): Ultra-fast, low resource usage
- **🟢 Small** (2B-3B): Balanced speed and quality  
- **🟡 Medium** (3B-8B): High-quality responses
- **🔴 Large** (> 8B): Premium quality, resource intensive
- **💻 Code**: Specialized for programming tasks

## 📊 Features

### Chat Interface
- Interactive multi-turn conversations
- Streaming responses with real-time display
- Model-specific prompt formatting
- Conversation history and persistence
- Rich terminal output with syntax highlighting

### Model Management
- **Dual Backend Support**: Ollama and MLX backends with unified interface
- **Rate Limit Avoidance**: Ollama backend bypasses Hugging Face restrictions
- Automatic model categorization and metadata
- Intelligent caching and cleanup
- Model search and filtering with short aliases
- Size estimation and resource planning
- Registry-based tracking for both backends
- Convenient CLI with both full commands and single-letter shortcuts

### Performance Benchmarking
- Comprehensive performance metrics
- Multi-model comparison
- System resource monitoring
- Detailed reporting and visualization
- Export results to JSON

### System Integration
- macOS-specific optimizations
- GPU memory management
- Thermal state monitoring
- Environment validation
- Automatic directory setup

## 🚦 Requirements

### System Requirements
- **OS**: macOS 12.0+ (Monterey) with Apple Silicon
- **Memory**: 8GB+ recommended (4GB minimum)
- **Storage**: 20GB+ free space
- **Python**: 3.10 or higher

### Model Requirements
- **Tiny models**: 2GB RAM, ~1GB storage
- **Small models**: 4GB RAM, ~2GB storage  
- **Medium models**: 8GB RAM, ~4GB storage
- **Large models**: 16GB+ RAM, ~8GB+ storage

## 🔮 Roadmap

- [x] **Dual Backend Architecture**: Ollama + MLX support
- [x] **Rate Limit Solution**: Ollama backend implementation
- [ ] **Ollama→MLX Conversion**: Convert Ollama models to MLX format
- [ ] **Backend Auto-switching**: Intelligent backend selection
- [ ] **Web Interface**: React-based web UI for remote access
- [ ] **API Server**: FastAPI backend for programmatic access
- [ ] **Plugin System**: Extensible architecture for custom tools
- [ ] **Model Fine-tuning**: Local model training and adaptation
- [ ] **Multi-modal Support**: Image and document processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the existing architecture
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Submit a pull request

### Development Guidelines
- Follow the existing modular architecture
- Keep modules under 200 lines of code
- Add type hints and docstrings
- Write tests for new functionality
- Update configuration as needed

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Ollama Team**: For the excellent local LLM management platform
- **MLX Team**: For the outstanding Apple Silicon ML framework
- **Hugging Face**: For the transformers ecosystem and model hub
- **Rich**: For beautiful terminal output
- **Typer**: For elegant CLI development

---

**ehAye Local** - Dual Backend LLM Interface: Ollama + MLX 🚀