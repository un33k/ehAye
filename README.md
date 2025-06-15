# ehAye Local

A modular, professional-grade LLM interface optimized for Apple Silicon with MLX.

## 🚀 Quick Start

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10 or higher

### Installation

1. **Bootstrap the environment:**
   ```bash
   ./bootstrap.sh
   ```

2. **Activate the environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Download a model:**
   ```bash
   ehaye-models search
   ehaye-models download phi2  # or any model alias
   ```

4. **Start chatting:**
   ```bash
   ehaye-chat interactive
   ```

## 🏗️ Architecture

ehAye Local follows a clean, modular architecture with strict separation of concerns:

```
src/
├── core/           # Configuration, environment, logging, exceptions
├── models/         # Model management (download, categorization, registry)
├── llm/           # LLM operations (chat, generation, prompts, streaming)
├── benchmarks/    # Performance testing and reporting
├── system/        # System monitoring and macOS integration
└── cli/           # Command-line interfaces
```

### Key Principles
- **Modular Design**: Each module is self-contained and under 200 lines
- **Configuration-Driven**: TOML-based configuration system
- **Professional Standards**: Type hints, error handling, logging, tests
- **Apple Silicon Optimized**: Native MLX integration and GPU utilization

## 📦 Available Commands

### Chat Interface
```bash
ehaye-chat interactive              # Interactive chat session
ehaye-chat single "Your question"   # Single prompt
ehaye-chat models                   # List available models
```

### Model Management
```bash
ehaye-models list                   # List installed models
ehaye-models search [query]         # Search available models
ehaye-models download <model-id>    # Download and install
ehaye-models remove <model-id>      # Remove model
ehaye-models info <model-id>        # Show model details
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
- Automatic model categorization and metadata
- Intelligent caching and cleanup
- Model search and filtering
- Size estimation and resource planning
- Registry-based tracking

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

- [ ] **Web Interface**: React-based web UI for remote access
- [ ] **API Server**: FastAPI backend for programmatic access
- [ ] **Plugin System**: Extensible architecture for custom tools
- [ ] **Model Fine-tuning**: Local model training and adaptation
- [ ] **Multi-modal Support**: Image and document processing
- [ ] **Distributed Computing**: Multi-device model execution

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

- **MLX Team**: For the excellent Apple Silicon ML framework
- **Hugging Face**: For the transformers ecosystem and model hub
- **Rich**: For beautiful terminal output
- **Typer**: For elegant CLI development

---

**ehAye Local** - Professional LLM interface for Apple Silicon 🚀