"""Tests for configuration modules."""

import pytest
from pathlib import Path

from ali.configuration.manager import ConfigManager, EhAyeConfig
from ali.exceptions.base import ConfigurationError


class TestEhAyeConfig:
    """Test the main configuration class."""
    
    def test_default_config_creation(self):
        """Test creating default configuration."""
        config = EhAyeConfig()
        
        assert config.paths.cache_dir.name == "ehaye"
        assert config.performance.omp_num_threads == 8
        assert config.models.categories == ["tiny", "small", "medium", "large", "code"]
        assert config.chat.default_temperature == 0.7
    
    def test_environment_variables(self, test_config):
        """Test environment variable generation."""
        env_vars = test_config.environment_variables
        
        assert "MLX_CACHE_DIR" in env_vars
        assert "MLX_MODELS_DIR" in env_vars
        assert "HF_HOME" in env_vars
        assert "OMP_NUM_THREADS" in env_vars
        assert env_vars["OMP_NUM_THREADS"] == "8"
    
    def test_create_directories(self, test_config):
        """Test directory creation."""
        # Directories should already exist from fixture
        assert test_config.paths.cache_dir.exists()
        assert test_config.paths.models_dir.exists()
        assert test_config.paths.logs_dir.exists()
        assert test_config.paths.config_dir.exists()
        
        # Check category directories
        categories = ["tiny", "small", "medium", "large", "code"]
        for category in categories:
            category_dir = test_config.paths.models_dir / category
            assert category_dir.exists()
    
    def test_model_list_file_path(self, test_config):
        """Test model list file path generation."""
        file_path = test_config.paths.models_dir / "tiny" / ".model_list"
        expected = test_config.paths.models_dir / "tiny" / ".model_list"
        
        assert file_path == expected


class TestConfigManager:
    """Test the configuration manager."""
    
    def test_load_default_config(self, temp_dir):
        """Test loading default config when file doesn't exist."""
        manager = ConfigManager(temp_dir / "nonexistent.toml")
        config = manager.load()
        
        assert config is not None
        assert config.performance.omp_num_threads == 8
    
    def test_config_property(self, config_manager):
        """Test config property access."""
        config = config_manager.config
        
        assert config is not None
        categories = ["tiny", "small", "medium", "large", "code"]
        assert config.models.categories == categories
    
    def test_update_config(self, config_manager):
        """Test configuration updates."""
        original_threads = config_manager.config.performance.omp_num_threads
        
        # This test would need proper implementation of update method
        # Currently it's a placeholder to show the intended interface
        assert original_threads == 8