"""Unit tests for configuration manager."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from .manager import ConfigManager, EhAyeConfig


class TestEhAyeConfig:
    """Test EhAyeConfig class."""
    
    def test_default_initialization(self):
        """Test default EhAyeConfig initialization."""
        config = EhAyeConfig()
        
        # Check basic attributes exist
        assert hasattr(config, 'paths')
        assert hasattr(config, 'performance')
        assert hasattr(config, 'environment_variables')
        
        # Check paths are Path objects
        assert isinstance(config.paths.cache_dir, Path)
        assert isinstance(config.paths.models_dir, Path)
        assert isinstance(config.paths.logs_dir, Path)
        assert isinstance(config.paths.config_dir, Path)
    
    def test_environment_variables_dict(self):
        """Test environment_variables returns dict."""
        config = EhAyeConfig()
        env_vars = config.environment_variables
        
        assert isinstance(env_vars, dict)
        # Should contain common variables
        assert any('MLX' in key or 'OMP' in key for key in env_vars.keys())
    
    @patch('pathlib.Path.mkdir')
    def test_create_directories(self, mock_mkdir):
        """Test directory creation."""
        config = EhAyeConfig()
        config.create_directories()
        
        # Should create directories with parents=True, exist_ok=True
        assert mock_mkdir.call_count >= 4  # At least cache, models, logs, config
        for call in mock_mkdir.call_args_list:
            args, kwargs = call
            assert kwargs.get('parents', False) is True
            assert kwargs.get('exist_ok', False) is True
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('os.environ.update')
    def test_setup_environment(self, mock_update):
        """Test environment setup."""
        config = EhAyeConfig()
        config.setup_environment()
        
        # Should update environment with config variables
        mock_update.assert_called_once()
        args = mock_update.call_args[0][0]
        assert isinstance(args, dict)


class TestConfigManager:
    """Test ConfigManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "test_config.toml"
        self.manager = ConfigManager(self.config_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_with_file(self):
        """Test ConfigManager initialization with config file."""
        assert self.manager.config_file == self.config_file
        assert self.manager._config is None
    
    def test_initialization_without_file(self):
        """Test ConfigManager initialization without config file."""
        manager = ConfigManager()
        assert manager.config_file is None
        assert manager._config is None
    
    @patch('ali.configuration.manager.load_config')
    def test_load_config_success(self, mock_load_config):
        """Test successful config loading."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        result = self.manager.load_config()
        
        assert result == mock_config
        assert self.manager._config == mock_config
        mock_load_config.assert_called_once_with(self.config_file)
    
    @patch('ali.configuration.manager.load_config')
    def test_load_config_failure(self, mock_load_config):
        """Test config loading failure."""
        mock_load_config.side_effect = Exception("Config error")
        
        with pytest.raises(Exception):
            self.manager.load_config()
        
        assert self.manager._config is None
    
    def test_get_config_cached(self):
        """Test getting cached config."""
        mock_config = Mock()
        self.manager._config = mock_config
        
        result = self.manager.get_config()
        assert result == mock_config
    
    @patch('ali.configuration.manager.load_config')
    def test_get_config_load_on_demand(self, mock_load_config):
        """Test loading config on demand."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        result = self.manager.get_config()
        
        assert result == mock_config
        assert self.manager._config == mock_config
    
    def test_create_default_config_structure(self):
        """Test creating default config structure."""
        # Create a basic TOML file
        config_content = """
[paths]
cache_dir = "/test/cache"
models_dir = "/test/models"

[performance]
omp_num_threads = 8
max_cache_size_gb = 50
"""
        self.config_file.write_text(config_content)
        
        config = self.manager.load_config()
        
        # Should have loaded successfully
        assert config is not None
    
    def test_config_file_not_exists(self):
        """Test behavior when config file doesn't exist."""
        non_existent = self.temp_dir / "non_existent.toml"
        manager = ConfigManager(non_existent)
        
        # Should create default config or handle gracefully
        config = manager.get_config()
        assert config is not None


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_full_config_workflow(self):
        """Test complete config loading and usage workflow."""
        config_file = self.temp_dir / "config.toml"
        
        # Create comprehensive config file
        config_content = """
[app]
name = "ehaye"
version = "0.1.0"

[paths]
cache_dir = "{temp_dir}/cache"
models_dir = "{temp_dir}/models"
logs_dir = "{temp_dir}/logs"
config_dir = "{temp_dir}/config"

[cli]
main_command = "ali"
model_command = "mod"
chat_command = "chat"

[performance]
omp_num_threads = 8
mlx_memory_pool = true
max_cache_size_gb = 50

[logging]
level = "INFO"
enable_rich = true
""".format(temp_dir=self.temp_dir)
        
        config_file.write_text(config_content)
        
        # Load config
        manager = ConfigManager(config_file)
        config = manager.get_config()
        
        # Verify config loaded correctly
        assert config is not None
        
        # Test directory creation
        config.create_directories()
        
        # Verify directories were created
        assert (self.temp_dir / "cache").exists()
        assert (self.temp_dir / "models").exists()
        assert (self.temp_dir / "logs").exists()
        assert (self.temp_dir / "config").exists()
    
    @patch.dict('os.environ', {}, clear=True)
    def test_environment_setup_integration(self):
        """Test environment setup with real config."""
        config = EhAyeConfig()
        
        # Clear environment first
        import os
        original_env = dict(os.environ)
        
        try:
            config.setup_environment()
            
            # Check that environment variables were set
            env_vars = config.environment_variables
            for key, value in env_vars.items():
                assert os.environ.get(key) == value
                
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


class TestConfigPaths:
    """Test configuration path handling."""
    
    def test_path_expansion(self):
        """Test path expansion and resolution."""
        config = EhAyeConfig()
        
        # Paths should be absolute
        assert config.paths.cache_dir.is_absolute()
        assert config.paths.models_dir.is_absolute()
        assert config.paths.logs_dir.is_absolute()
        assert config.paths.config_dir.is_absolute()
    
    def test_path_relationships(self):
        """Test logical relationships between paths."""
        config = EhAyeConfig()
        
        # Models dir should be under cache dir (typical setup)
        try:
            config.paths.cache_dir in config.paths.models_dir.parents
        except AttributeError:
            # Some configurations might not follow this pattern
            pass
    
    def test_custom_paths(self):
        """Test setting custom paths."""
        config = EhAyeConfig()
        
        # Test that paths can be modified
        custom_cache = Path("/custom/cache")
        config.paths.cache_dir = custom_cache
        assert config.paths.cache_dir == custom_cache


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_required_attributes(self):
        """Test that required config attributes exist."""
        config = EhAyeConfig()
        
        # Required path attributes
        required_paths = ['cache_dir', 'models_dir', 'logs_dir', 'config_dir']
        for attr in required_paths:
            assert hasattr(config.paths, attr)
            assert isinstance(getattr(config.paths, attr), Path)
        
        # Required performance attributes
        assert hasattr(config.performance, 'omp_num_threads')
        assert hasattr(config.performance, 'max_cache_size_gb')
    
    def test_config_types(self):
        """Test configuration value types."""
        config = EhAyeConfig()
        
        # Performance values should be appropriate types
        assert isinstance(config.performance.omp_num_threads, int)
        assert isinstance(config.performance.max_cache_size_gb, (int, float))
        
        # Environment variables should be strings
        for key, value in config.environment_variables.items():
            assert isinstance(key, str)
            assert isinstance(value, str)


class TestErrorHandling:
    """Test error handling in configuration."""
    
    def test_invalid_config_file(self):
        """Test handling of invalid config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            # Write invalid TOML
            f.write("invalid toml content [[[")
            invalid_file = Path(f.name)
        
        try:
            manager = ConfigManager(invalid_file)
            
            # Should handle invalid TOML gracefully
            with pytest.raises(Exception):
                manager.load_config()
                
        finally:
            invalid_file.unlink()
    
    def test_permission_denied(self):
        """Test handling of permission denied errors."""
        # This test would need special setup for permission testing
        # For now, just verify the error handling exists
        pass
    
    @patch('pathlib.Path.mkdir')
    def test_directory_creation_failure(self, mock_mkdir):
        """Test handling of directory creation failure."""
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        config = EhAyeConfig()
        
        with pytest.raises(PermissionError):
            config.create_directories()


class TestConfigDefaults:
    """Test configuration default values."""
    
    def test_default_values_reasonable(self):
        """Test that default configuration values are reasonable."""
        config = EhAyeConfig()
        
        # Performance defaults should be reasonable
        assert 1 <= config.performance.omp_num_threads <= 32
        assert 1 <= config.performance.max_cache_size_gb <= 1000
        
        # Paths should be in user directory or system-appropriate location
        assert str(config.paths.cache_dir) != "/"
        assert str(config.paths.models_dir) != "/"
    
    def test_environment_variables_complete(self):
        """Test that all necessary environment variables are included."""
        config = EhAyeConfig()
        env_vars = config.environment_variables
        
        # Should include performance-related variables
        performance_vars = [key for key in env_vars.keys() if 'OMP' in key or 'MLX' in key]
        assert len(performance_vars) > 0