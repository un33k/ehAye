"""Exception classes for ehAye."""

from .base import (
    EhAyeError,
    ConfigurationError,
    EnvironmentError,
    ModelError,
    ModelNotFoundError,
    ModelLoadError,
    ModelDownloadError,
    SystemResourceError,
    VirtualEnvironmentError,
    GPUError,
    BenchmarkError,
    CLIError,
)

__all__ = [
    "EhAyeError",
    "ConfigurationError",
    "EnvironmentError",
    "ModelError",
    "ModelNotFoundError",
    "ModelLoadError",
    "ModelDownloadError",
    "SystemResourceError",
    "VirtualEnvironmentError",
    "GPUError",
    "BenchmarkError",
    "CLIError",
]