"""Integration tests for system CLI."""

import pytest
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from ali.cli.system_cli import app


class TestSystemCLI:
    """Test system CLI commands."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    @patch('ali.cli.system_cli.get_system_info')
    def test_info_command(self, mock_get_info):
        """Test system info command."""
        # Mock system info
        mock_info = {
            "memory": {
                "total_gb": 16.0,
                "available_gb": 8.0,
                "used_percent": 50.0,
                "process_mb": 100.0
            },
            "cpu": {
                "brand": "Test CPU",
                "count": 8,
                "count_logical": 16,
                "usage_percent": 25.0
            },
            "gpu": {
                "available": True,
                "memory_mb": 8192,
                "memory_gb": 8.0
            },
            "thermal_state": "nominal"
        }
        
        mock_get_info.return_value = mock_info
        
        result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "System Information" in result.output
        assert "16.0GB" in result.output
        assert "Test CPU" in result.output
    
    @patch('ali.cli.system_cli.validate_benchmark_environment')
    def test_validate_command(self, mock_validate_bench):
        """Test system validation command."""
        mock_validate_bench.return_value = True
        
        result = self.runner.invoke(app, ["validate"])
        
        assert result.exit_code == 0
        assert "System Environment Validation" in result.output
        assert "✅" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    def test_config_command(self, mock_get_config):
        """Test config display command."""
        # Mock config
        mock_config = MagicMock()
        mock_config.paths.cache_dir = "/test/cache"
        mock_config.paths.models_dir = "/test/models"
        mock_config.paths.logs_dir = "/test/logs"
        mock_config.paths.config_dir = "/test/config"
        mock_config.environment_variables = {
            "MLX_CACHE_DIR": "/test/cache/mlx",
            "OMP_NUM_THREADS": "8"
        }
        mock_config.performance.omp_num_threads = 8
        mock_config.performance.mlx_memory_pool = True
        mock_config.performance.max_cache_size_gb = 50
        
        mock_get_config.return_value = mock_config
        
        result = self.runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        assert "Configuration" in result.output
        assert "/test/cache" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    def test_setup_command(self, mock_get_config):
        """Test system setup command."""
        # Mock config
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config
        
        result = self.runner.invoke(app, ["setup"])
        
        assert result.exit_code == 0
        assert "System Setup" in result.output
        
        # Verify config methods were called
        mock_config.create_directories.assert_called_once()
        mock_config.setup_environment.assert_called_once()
    
    def test_help_command(self):
        """Test help command."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "System management and diagnostics" in result.output
        assert "info" in result.output
        assert "validate" in result.output
        assert "config" in result.output
        assert "setup" in result.output