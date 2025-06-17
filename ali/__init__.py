"""ehAye - Local LLM interface with dual backend support."""

__version__ = "0.1.0"

# Core modules
from . import configuration
from . import logging
from . import exceptions

# Backend support
from . import backends

# LLM functionality  
from . import llm
from . import models
from . import benchmarking

# CLI interface
from . import cli

__all__ = [
    "configuration",
    "logging", 
    "exceptions",
    "backends",
    "llm",
    "models", 
    "benchmarking",
    "cli",
]