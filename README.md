# ehAye Local

A modular, professional-grade LLM interface with dual backend support: Ollama for easy model access and MLX for Apple Silicon optimization.

## 🚀 Quick Start

### Prerequisites
- macOS with Apple Silicon (M1/M2/M3/M4)
- Python 3.10 or higher
- Terminal with 256-color support (recommended)

### Installation

1. **Bootstrap everything (installs Python, MLX, Ollama, and ehAye Local):**
   ```bash
   ./bootstrap.sh
   ```

2. **Activate the environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Download a model:**
   ```bash
   # Ali - Artificial Line Interface
   ali mod search -q phi          # Search for phi models
   ali mod download -m phi3:mini  # Download phi3:mini
   
   # Or use Ollama directly
   ali olla pull phi3
   ```

4. **Check system info:**
   ```bash
   ali sys info                    # View system resources
   ```

5. **Start chatting:**
   ```bash
   ali chat interactive            # Interactive chat session
   ```

6. **Use direct Ollama commands (NEW!):**
   ```bash
   ali olla -- --version          # Pass commands directly to Ollama
   ali olla -- show phi3          # Use any Ollama command seamlessly
   ```

## ⚡ Quick CLI Usage

### Ali - Artificial Line Interface
```bash
# Model management
ali mod list                         # List models
ali mod search -q phi                # Search for phi models
ali mod download -m phi3:mini        # Download phi3:mini
ali mod remove -m old-model --force  # Remove model
ali mod info -m phi3:mini            # Show model info

# With specific providers (default: ollama)
ali mod search -p ollama             # Search Ollama models
ali mod search -p mlx                # Search MLX models
ali mod download -m phi3 -p ollama   # Download via Ollama
ali mod remove -m phi2 -p mlx        # Remove MLX model

# Chat interface
ali chat interactive                 # Interactive chat
ali chat single "Hello world"        # Single prompt
ali chat models                      # List chat models

# Performance benchmarking
ali perf single -m phi3:mini         # Benchmark single model
ali perf compare --all               # Compare all models
ali perf validate                    # Check environment

# System management
ali sys info                         # System information (CPU, GPU, Memory)
ali sys validate                     # Environment validation
ali sys config                      # Show configuration
ali sys setup                       # Initialize system
ali sys cleanup --logs --cache       # Clean up files

# Direct Ollama operations
ali olla pull phi3                   # Download via Ollama
ali olla run phi3                    # Chat via Ollama
ali olla list                        # List Ollama models
ali olla start                       # Start Ollama service

# Direct parameter passthrough to Ollama
ali olla -- --version               # Pass --version directly to ollama
ali olla -- --help                  # Pass --help directly to ollama  
ali olla -- create mymodel -f Modelfile  # Pass complex commands directly
```

### Direct Ollama Operations
```bash
ali olla pull phi3                    # Download model
ali olla run phi3                     # Interactive chat
ali olla list                         # List models
ali olla start                        # Start service
ali olla stop                         # Stop service
ali olla ps                           # Show running processes

# Direct parameter passthrough (NEW!)
ali olla -- --version                # Get Ollama version
ali olla -- --help                   # Get Ollama help
ali olla -- create mymodel -f Modelfile  # Create model from Modelfile
ali olla -- show phi3 --modelfile    # Show model with specific options
ali olla -- ps                       # Direct ps command
```

## 🏗️ Architecture

ehAye Local follows a clean, modular architecture with dual backend support:

```
ali/
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
ali chat interactive                 # Interactive chat session
ali chat single "Your question"      # Single prompt
ali chat models                      # List available models
```

### Model Management
```bash
# Basic commands
ali mod list                        # List installed models
ali mod search -q phi               # Search for phi models
ali mod download -m phi3:mini       # Download phi3:mini
ali mod remove -m old-model --force # Remove model
ali mod info -m phi3:mini           # Show model info

# With specific providers
ali mod list -p ollama              # List Ollama models
ali mod search -p mlx               # Search MLX models
ali mod download -m phi3 -p ollama  # Download via Ollama
ali mod remove -m phi2 -p mlx       # Remove MLX model
```

### Direct Ollama Operations
```bash
ali olla pull phi3                  # Download model directly
ali olla run phi3                   # Start interactive chat
ali olla list                       # List all models
ali olla start                      # Start Ollama service
ali olla stop                       # Stop Ollama service
ali olla ps                         # Show running processes
ali olla remove phi3                # Remove model
ali olla info phi3                  # Show model info

# Direct parameter passthrough to Ollama (NEW!)
ali olla -- --version              # Get Ollama version directly
ali olla -- --help                 # Get Ollama help directly
ali olla -- create mymodel -f Modelfile  # Pass complex commands
ali olla -- show phi3 --modelfile  # Use Ollama-specific options
```

### Performance Benchmarking
```bash
ali perf single -m <model>          # Benchmark single model
ali perf compare --all              # Compare all models
ali perf validate                   # Check environment
```

### System Management
```bash
ali sys info                        # Detailed system information
ali sys validate                    # Environment validation
ali sys config --paths             # Show configured paths
ali sys config --env               # Show environment variables
ali sys setup                      # Initialize system
ali sys cleanup --logs --cache      # Clean up system files
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
├── ali/                    # Main source code
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
pytest -v --cov=ali        # With coverage

# Test specific functionality
ali sys validate            # Test system environment
ali mod list                # Test model detection
ali sys info                # Test system information
```

### Code Quality
```bash
ruff check ali/             # Linting
black ali/                  # Code formatting
mypy ali/                   # Type checking
```

## 🎯 Model Categories

- **🔵 Tiny** (< 2B): Ultra-fast, low resource usage
- **🟢 Small** (2B-3B): Balanced speed and quality  
- **🟡 Medium** (3B-8B): High-quality responses
- **🔴 Large** (> 8B): Premium quality, resource intensive
- **💻 Code**: Specialized for programming tasks

## 📊 Features

### Enhanced CLI Experience
- **Clean Interface**: No verbose logging by default
- **Debug Modes**: Use `--verbose` or `--debug` for detailed output
- **Rich Display**: Beautiful terminal output with aligned formatting
- **System Info**: Comprehensive hardware information including GPU cores

### Chat Interface
- Interactive multi-turn conversations
- Streaming responses with real-time display
- Model-specific prompt formatting
- Clean error handling without log spam
- Rich terminal output with syntax highlighting

### Model Management
- **Dual Backend Support**: Ollama and MLX backends with unified interface
- **Rate Limit Avoidance**: Ollama backend bypasses Hugging Face restrictions
- **Clean Error Handling**: User-friendly messages without debug spam
- Automatic model categorization and metadata
- Intelligent caching and cleanup
- Model search and filtering with short aliases
- Size estimation and resource planning
- Registry-based tracking for both backends

### Direct Ollama Integration
- **Parameter Passthrough**: Use `ali olla -- <params>` to pass any Ollama command directly
- **Full Ollama Compatibility**: Access all Ollama features without switching tools
- **Seamless Workflow**: Mix ehAye commands with native Ollama operations
- **No Learning Curve**: Use familiar Ollama syntax within ehAye Local
- **Advanced Features**: Access Ollama's latest features immediately

### Performance Benchmarking
- Comprehensive performance metrics
- Multi-model comparison
- System resource monitoring
- Detailed reporting and visualization
- Export results to JSON

### System Integration
- **Apple Silicon Optimization**: M1/M2/M3/M4 specific features
- **GPU Information**: Core count and allocated memory detection
- **Thermal Monitoring**: Real-time thermal state tracking
- **Environment Validation**: Comprehensive system checks
- **Clean Logging**: Debug info only when requested
- Automatic directory setup and configuration

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

### ✅ Completed
- [x] **Dual Backend Architecture**: Ollama + MLX support
- [x] **Rate Limit Solution**: Ollama backend implementation  
- [x] **Clean CLI Experience**: Minimal logging, rich formatting
- [x] **System Information**: GPU cores, memory allocation detection
- [x] **Error Handling**: User-friendly messages without debug spam
- [x] **Project Restructure**: Clean `ali/` package structure
- [x] **Ollama Parameter Passthrough**: Direct `ali olla -- <params>` functionality
- [x] **Click Migration**: Migrated from Typer to Click for advanced CLI features

### 🚧 In Progress
- [ ] **Ollama→MLX Conversion**: Convert Ollama models to MLX format
- [ ] **Backend Auto-switching**: Intelligent backend selection

### 📋 Planned
- [ ] **Web Interface**: React-based web UI for remote access
- [ ] **API Server**: FastAPI backend for programmatic access
- [ ] **Plugin System**: Extensible architecture for custom tools
- [ ] **Model Fine-tuning**: Local model training and adaptation
- [ ] **Multi-modal Support**: Image and document processing
- [ ] **Performance Optimization**: Enhanced Apple Silicon utilization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes following the existing architecture
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Submit a pull request

### Development Guidelines
- Follow the existing modular architecture in `ali/`
- Keep modules under 200 lines of code
- Add type hints and docstrings
- Use `--debug` for development logging
- Write tests for new functionality
- Maintain clean user experience (no verbose logs by default)
- Update configuration as needed

### Development Workflow
```bash
# Use editable install for development
pip install -e .

# Test changes immediately (no reinstall needed)
ali --debug sys info

# Run quality checks
ruff check ali/
mypy ali/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Ollama Team**: For the excellent local LLM management platform
- **MLX Team**: For the outstanding Apple Silicon ML framework
- **Hugging Face**: For the transformers ecosystem and model hub
- **Rich**: For beautiful terminal output
- **Click**: For powerful CLI framework with advanced argument handling
- **Typer**: For initial CLI development foundation

---

**ehAye Local** - Dual Backend LLM Interface: Ollama + MLX 🚀