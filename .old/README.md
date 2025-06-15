# Legacy Files

This directory contains the original files from before the architectural refactoring.

## What's Here

### Original Python Scripts
- `benchmark.py` - Original monolithic benchmark script
- `chat.py` - Original chat interface (21K lines)
- `performance-test.py` - System performance tests
- `mlx_config.py` - Old configuration system

### Original Shell Scripts
- `brew.sh` - Homebrew installation script
- `llm.sh` - Model management script (37K lines)
- `mlx.sh` - MLX setup script
- `mlx-env.sh` / `mlx_env.sh` - Environment setup
- `venv.sh` - Virtual environment management (18K lines)

### Configuration
- `mlx-config.json` - Old JSON-based configuration

### Documentation
- `spec-*.md` - Various specification documents
- `layout.md` - Original project layout documentation

### Models Directory
- `models/` - Original model storage structure

## Migration Notes

These files have been refactored into the new modular architecture:

- **Old monolithic scripts** → **Modular src/ packages**
- **Single large files** → **Multiple focused modules (<200 lines each)**
- **JSON config** → **TOML configuration system**
- **Bash-heavy approach** → **Python-first with minimal bootstrap**

## Reference

Keep these files for reference during the transition period. They can be safely removed once the new system is fully validated and operational.

---

*Files moved during architectural refactoring on 2025-06-15*