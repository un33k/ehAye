"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from ali.configuration.manager import ConfigManager, EhAyeConfig


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration."""
    config = EhAyeConfig()
    
    # Override paths to use temp directory
    config.paths.cache_dir = temp_dir / "cache"
    config.paths.models_dir = temp_dir / "models"
    config.paths.logs_dir = temp_dir / "logs"
    config.paths.config_dir = temp_dir / "config"
    
    # Create test directories
    config.paths.cache_dir.mkdir(parents=True, exist_ok=True)
    config.paths.models_dir.mkdir(parents=True, exist_ok=True)
    config.paths.logs_dir.mkdir(parents=True, exist_ok=True)
    config.paths.config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create category directories
    categories = ["tiny", "small", "medium", "large", "code"]
    for category in categories:
        category_dir = config.paths.models_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
    
    return config


@pytest.fixture
def config_manager(test_config, temp_dir):
    """Create a test config manager."""
    manager = ConfigManager()
    manager._config = test_config
    manager.config_file = temp_dir / "test_settings.toml"
    return manager


@pytest.fixture
def sample_model_id():
    """Sample model ID for testing."""
    return "test-org/test-model-1b"


@pytest.fixture
def sample_models():
    """Sample model list for testing."""
    return [
        "test-org/tiny-model-500m",
        "test-org/small-model-2b",
        "test-org/medium-model-7b",
        "test-org/large-model-13b",
        "test-org/code-model-6b"
    ]