# ehAye - Local LLM Interface

A professional-grade local LLM interface optimized for Apple Silicon Macs, featuring dual backend support (Ollama + MLX) and comprehensive model management.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Apple Silicon](https://img.shields.io/badge/Apple_Silicon-M1%2FM2%2FM3%2FM4-red.svg)](https://developer.apple.com/apple-silicon/)
[![Tests](https://img.shields.io/badge/tests-800%2B-green.svg)](./tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

## ⚡ Quick Start

### Installation

**Option 1: Automatic Setup (Recommended)**
```bash
git clone <repository-url>
cd ehAye
./bootstrap.sh
source .venv/bin/activate
```

**Option 2: Manual Setup**
```bash
git clone <repository-url>
cd ehAye
pip install -e .
```

### First Steps

```bash
# Verify installation
ali --help

# Check system resources
ali sys info

# Install your first model
ali olla pull qwen2:0.5b

# Start chatting
ali chat
```

## 🎯 Core Features

### 🤖 **Dual Backend System**
- **Ollama**: Easy model management, bypasses rate limits
- **MLX**: Apple Silicon optimized inference (M1/M2/M3/M4)
- **Unified CLI**: Same commands work with both backends

### 💬 **Interactive Chat**
- Real-time streaming responses
- Model auto-detection and selection
- Clean, intuitive interface
- Support for all Ollama models

### 📦 **Smart Model Management**
- Search, download, and organize models
- Automatic categorization (tiny/small/medium/large/code)
- Direct Ollama command passthrough
- Storage and performance optimization

### 🔧 **Professional Tools**
- System monitoring and diagnostics
- Performance benchmarking
- Comprehensive error handling
- Rich terminal output

## 📋 Command Overview

### Chat Interface
```bash
ali chat                           # Interactive chat with model selection
ali chat interactive -m qwen2:0.5b # Chat with specific model
ali chat single "Hello world"      # Single prompt mode
```

### Model Management
```bash
ali mod list                       # List installed models
ali mod search -q phi              # Search for models
ali mod download -m phi3:mini      # Download a model
ali mod info -m phi3:mini          # Show model details
```

### Direct Ollama Access
```bash
ali olla pull phi3:mini            # Download model
ali olla list                      # List models
ali olla run phi3:mini             # Interactive chat
ali olla -- --version             # Pass any Ollama command
```

### System Management
```bash
ali sys info                       # Hardware info (CPU/GPU/Memory)
ali sys validate                   # Environment check
ali sys config                     # Show configuration
ali sys setup                      # Initialize system
```

### Performance Testing
```bash
ali perf single -m qwen2:0.5b      # Benchmark single model
ali perf compare --all             # Compare all models
ali perf validate                   # Check benchmark environment
```

## 🏗️ Architecture

ehAye follows a clean, modular architecture:

```
ali/
├── cli/                    # Command-line interfaces (Click-based)
├── backends/               # Backend implementations (Ollama/MLX)
├── configuration/          # TOML-based configuration system
├── logging/                # Rich logging with multiple formatters
├── chat/                   # Chat session management
├── models/                 # Model registry and management
├── benchmarking/           # Performance testing tools
├── utilities/              # Shared utilities and helpers
└── exceptions/             # Comprehensive error handling
```

### Design Principles
- **800+ Unit Tests**: Co-located with source code for easy maintenance
- **Type Safety**: Full type hints with mypy strict mode
- **Modular Design**: Each module under 200 lines for maintainability
- **Professional Quality**: Industry-standard patterns and practices

## 💡 Usage Examples

### Quick Model Testing
```bash
# Download a small, fast model for testing
ali olla pull qwen2:0.5b

# Test it immediately
ali chat interactive -m qwen2:0.5b

# Or use single prompts
ali chat single "Explain quantum computing" -m qwen2:0.5b
```

### Model Discovery
```bash
# Search for specific models
ali mod search -q deepseek -f 7B
ali mod search -f 1B              # Find small models
ali mod search -c code            # Find code-specialized models

# Check available models
ali olla list
```

### System Optimization
```bash
# Check your system capabilities
ali sys info

# Validate environment
ali sys validate

# Clean up storage
ali sys cleanup --logs --cache
```

### Advanced Ollama Integration
```bash
# Use any Ollama command directly
ali olla -- create mymodel -f Modelfile
ali olla -- show phi3 --modelfile
ali olla -- --help

# Standard Ollama operations
ali olla start                     # Start Ollama service
ali olla ps                        # Show running models
ali olla stop phi3                 # Stop specific model
```

## ⚙️ Configuration

ehAye uses TOML configuration files in the `config/` directory:

### Main Settings (`config/app.toml`)
```toml
[app]
name = "ehaye"
version = "0.1.0"

[cli]
main_command = "ali"
model_command = "mod"
chat_command = "chat"

[performance]
omp_num_threads = 8
mlx_memory_pool = true
max_cache_size_gb = 50
```

### Model Categories
- **🔵 Tiny** (< 2B): Ultra-fast, low resource (qwen2:0.5b, llama3.2:1b)
- **🟢 Small** (2B-3B): Balanced speed/quality (phi3:mini, gemma2:2b)
- **🟡 Medium** (3B-8B): High quality (llama3.1:8b, deepseek-coder:6.7b)
- **🔴 Large** (> 8B): Premium quality (llama3.1:70b, qwen2.5:72b)
- **💻 Code**: Programming specialized (deepseek-coder, codellama)

## 🧪 Testing

ehAye includes comprehensive test coverage:

```bash
# Run all tests (800+ test cases)
pytest

# Run specific test categories
pytest ali/cli/                   # CLI tests (co-located)
pytest tests/unit/                # Traditional unit tests
pytest tests/integration/         # Integration tests

# Run with coverage
pytest --cov=ali

# Test specific functionality
pytest ali/cli/test_chat_cli.py::TestChatSession
```

### Test Architecture
- **Co-located Tests**: Unit tests next to source files (`ali/*/test_*.py`)
- **Integration Tests**: End-to-end workflow testing (`tests/integration/`)
- **Comprehensive Coverage**: CLI, backends, configuration, logging, chat

## 🚀 Development

### Setup Development Environment
```bash
# Clone and setup
git clone <repository-url>
cd ehAye
./bootstrap.sh
source .venv/bin/activate

# Install development dependencies
pip install -e .[dev]

# Run code quality checks
ruff check ali/                   # Linting
black ali/                        # Formatting
mypy ali/                         # Type checking
```

### Code Quality Standards
- **Type Hints**: All functions and classes fully typed
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: New features require corresponding tests
- **Modularity**: Keep modules focused and under 200 lines
- **Error Handling**: User-friendly messages with proper logging

### Project Structure
```
ehAye/
├── ali/                         # Main package
│   ├── cli/test_*.py           # Co-located CLI tests
│   ├── configuration/test_*.py # Co-located config tests
│   └── */test_*.py            # All modules have co-located tests
├── tests/                      # Traditional test structure
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test data and fixtures
├── config/                     # Configuration files
├── scripts/                    # Utility scripts
└── pyproject.toml             # Modern Python project configuration
```

## 🎯 System Requirements

### Hardware
- **CPU**: Apple Silicon (M1/M2/M3/M4) or Intel Mac
- **Memory**: 8GB+ recommended (4GB minimum)
- **Storage**: 20GB+ free space for models
- **OS**: macOS 12.0+ (Monterey)

### Software
- **Python**: 3.10 or higher
- **Terminal**: 256-color support recommended
- **Ollama**: Automatically managed by ehAye

### Model Requirements
| Category | RAM Required | Storage | Example Models |
|----------|-------------|---------|----------------|
| Tiny     | 2GB         | ~500MB  | qwen2:0.5b, llama3.2:1b |
| Small    | 4GB         | ~2GB    | phi3:mini, gemma2:2b |
| Medium   | 8GB         | ~4GB    | llama3.1:8b, deepseek-coder:6.7b |
| Large    | 16GB+       | ~8GB+   | llama3.1:70b, qwen2.5:72b |

## 🗺️ Roadmap

### ✅ Current (v0.1.0)
- [x] Complete CLI interface with Click framework
- [x] Ollama backend with direct command passthrough
- [x] Interactive chat with streaming responses
- [x] Model management and categorization
- [x] System monitoring and diagnostics
- [x] 800+ comprehensive unit tests
- [x] Professional code quality standards

### 🚧 Next (v0.2.0)
- [ ] MLX backend implementation and optimization
- [ ] Model format conversion (Ollama → MLX)
- [ ] Advanced benchmarking and performance analysis
- [ ] Web interface for remote access

### 🔮 Future
- [ ] Plugin system for extensibility
- [ ] Model fine-tuning capabilities
- [ ] Multi-modal support (vision, audio)
- [ ] API server for programmatic access

## 🤝 Contributing

We welcome contributions! Please see our [contribution guidelines](CONTRIBUTING.md).

### Quick Contribution Guide
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **[Ollama](https://ollama.ai/)** - Excellent local LLM platform
- **[MLX](https://ml-explore.github.io/mlx/)** - Apple Silicon ML framework
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal output
- **[Click](https://click.palletsprojects.com/)** - Powerful CLI framework

---

**ehAye** - Professional Local LLM Interface for Apple Silicon 🚀