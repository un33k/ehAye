"""Unit tests for system CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from click.testing import CliRunner

from .system_cli import (
    get_system_info,
    validate_benchmark_environment,
    app
)


class TestSystemInfo:
    """Test system information functions."""
    
    def test_get_system_info_structure(self):
        """Test get_system_info returns expected structure."""
        info = get_system_info()
        
        # Check required keys exist
        assert "memory" in info
        assert "cpu" in info
        assert "gpu" in info
        assert "thermal_state" in info
        
        # Check memory structure
        memory = info["memory"]
        assert "total_gb" in memory
        assert "available_gb" in memory
        assert "used_percent" in memory
        assert "process_mb" in memory
        
        # Check CPU structure
        cpu = info["cpu"]
        assert "brand" in cpu
        assert "count" in cpu
        assert "count_logical" in cpu
        assert "usage_percent" in cpu
        
        # Check GPU structure
        gpu = info["gpu"]
        assert "available" in gpu
        assert "memory_mb" in gpu
        assert "memory_gb" in gpu
        assert "cores" in gpu
    
    def test_get_system_info_values(self):
        """Test get_system_info returns reasonable values."""
        info = get_system_info()
        
        # Check memory values are reasonable
        memory = info["memory"]
        assert memory["total_gb"] > 0
        assert memory["available_gb"] >= 0
        assert 0 <= memory["used_percent"] <= 100
        assert memory["process_mb"] > 0
        
        # Check CPU values
        cpu = info["cpu"]
        assert cpu["count"] > 0
        assert cpu["count_logical"] >= cpu["count"]
        assert 0 <= cpu["usage_percent"] <= 100
        
        # Check thermal state is valid
        assert info["thermal_state"] in ["nominal", "fair", "serious", "critical"]
    
    def test_validate_benchmark_environment(self):
        """Test benchmark environment validation."""
        result = validate_benchmark_environment()
        assert isinstance(result, bool)


class TestSystemCLI:
    """Test system CLI commands."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_app_help(self):
        """Test system app help command."""
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert "System management and diagnostics" in result.output
        assert "info" in result.output
        assert "validate" in result.output
        assert "config" in result.output
        assert "setup" in result.output
        assert "cleanup" in result.output
    
    @patch('ali.cli.system_cli.get_system_info')
    @patch('ali.cli.system_cli.common_setup')
    def test_info_command(self, mock_setup, mock_get_info):
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
                "brand": "Apple M1",
                "count": 8,
                "count_logical": 8,
                "usage_percent": 25.0
            },
            "gpu": {
                "available": True,
                "memory_mb": 7168,
                "memory_gb": 7.0,
                "cores": 8
            },
            "thermal_state": "nominal"
        }
        
        mock_get_info.return_value = mock_info
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "System Information" in result.output
        assert "16.0GB" in result.output
        assert "Apple M1" in result.output
        assert "7168MB" in result.output
        assert "nominal" in result.output.lower()
    
    @patch('ali.cli.system_cli.validate_benchmark_environment')
    @patch('ali.cli.system_cli.common_setup')
    def test_validate_command_success(self, mock_setup, mock_validate_bench):
        """Test successful system validation command."""
        mock_validate_bench.return_value = True
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["validate"])
        
        assert result.exit_code == 0
        assert "System Environment Validation" in result.output
        assert "✅" in result.output
        assert "All validation checks passed" in result.output
    
    @patch('ali.cli.system_cli.validate_benchmark_environment')
    @patch('ali.cli.system_cli.common_setup')
    @patch('psutil.virtual_memory')
    def test_validate_command_with_checks(self, mock_memory, mock_setup, mock_validate_bench):
        """Test validation command with detailed checks."""
        # Mock memory to have enough RAM
        mock_memory.return_value.total = 16 * 1024**3  # 16GB
        mock_validate_bench.return_value = True
        mock_setup.return_value = Mock()
        
        with patch('sys.version_info', (3, 11, 0)):
            with patch.dict('os.environ', {'VIRTUAL_ENV': '/test/venv'}):
                result = self.runner.invoke(app, ["validate"])
        
        assert result.exit_code == 0
        assert "Python version: OK" in result.output
        assert "Virtual environment: OK" in result.output
        assert "System resources: OK" in result.output
    
    @patch('ali.cli.system_cli.validate_benchmark_environment')
    @patch('ali.cli.system_cli.common_setup')
    def test_validate_command_failures(self, mock_setup, mock_validate_bench):
        """Test validation command with failures."""
        mock_validate_bench.return_value = False
        mock_setup.return_value = Mock()
        
        with patch('sys.version_info', (3, 9, 0)):  # Old Python
            with patch.dict('os.environ', {}, clear=True):  # No venv
                result = self.runner.invoke(app, ["validate"])
        
        assert result.exit_code == 0
        assert "❌" in result.output
        assert "issue(s)" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    def test_config_command_default(self, mock_setup, mock_get_config):
        """Test config display command with default options."""
        # Mock config
        mock_config = Mock()
        mock_config.paths.cache_dir = Path("/test/cache")
        mock_config.paths.models_dir = Path("/test/models")
        mock_config.paths.logs_dir = Path("/test/logs")
        mock_config.paths.config_dir = Path("/test/config")
        mock_config.environment_variables = {
            "MLX_CACHE_DIR": "/test/cache/mlx",
            "OMP_NUM_THREADS": "8"
        }
        mock_config.performance.omp_num_threads = 8
        mock_config.performance.mlx_memory_pool = True
        mock_config.performance.max_cache_size_gb = 50
        
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["config"])
        
        assert result.exit_code == 0
        assert "Configuration" in result.output
        assert "/test/cache" in result.output
        assert "/test/models" in result.output
        assert "MLX_CACHE_DIR" in result.output
        assert "OMP Threads" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    def test_config_command_paths_only(self, mock_setup, mock_get_config):
        """Test config command with --paths flag."""
        mock_config = Mock()
        mock_config.paths.cache_dir = Path("/test/cache")
        mock_config.paths.models_dir = Path("/test/models")
        mock_config.paths.logs_dir = Path("/test/logs")
        mock_config.paths.config_dir = Path("/test/config")
        mock_config.environment_variables = {}
        mock_config.performance.omp_num_threads = 8
        mock_config.performance.mlx_memory_pool = True
        mock_config.performance.max_cache_size_gb = 50
        
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["config", "--paths"])
        
        assert result.exit_code == 0
        assert "Configured Paths" in result.output
        assert "/test/cache" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    def test_setup_command(self, mock_setup, mock_get_config):
        """Test system setup command."""
        # Mock config
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["setup"])
        
        assert result.exit_code == 0
        assert "System Setup" in result.output
        assert "setup completed" in result.output
        
        # Verify config methods were called
        mock_config.create_directories.assert_called_once()
        mock_config.setup_environment.assert_called_once()
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    @patch('click.confirm')
    def test_cleanup_command_logs(self, mock_confirm, mock_setup, mock_get_config):
        """Test cleanup command for logs."""
        mock_confirm.return_value = True
        mock_config = Mock()
        mock_config.paths.logs_dir = Path("/test/logs")
        mock_config.paths.cache_dir = Path("/test/cache")
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        # Mock Path.exists to return True
        with patch.object(Path, 'exists', return_value=True):
            with patch('shutil.rmtree'):
                with patch.object(Path, 'mkdir'):
                    result = self.runner.invoke(app, ["cleanup", "--logs"])
        
        assert result.exit_code == 0
        assert "Cleanup completed" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    def test_cleanup_command_no_options(self, mock_setup, mock_get_config):
        """Test cleanup command with no options."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["cleanup"])
        
        assert result.exit_code == 0
        assert "Specify what to clean" in result.output
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    @patch('click.confirm')
    def test_cleanup_command_cache(self, mock_confirm, mock_setup, mock_get_config):
        """Test cleanup command for cache."""
        mock_confirm.return_value = True
        mock_config = Mock()
        mock_config.paths.cache_dir = Path("/test/cache")
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        # Mock directory structure
        mock_item1 = Mock()
        mock_item1.name = "temp"
        mock_item1.is_dir.return_value = True
        mock_item2 = Mock()
        mock_item2.name = "models"  # Should be preserved
        mock_item2.is_dir.return_value = True
        
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'iterdir', return_value=[mock_item1, mock_item2]):
                with patch('shutil.rmtree') as mock_rmtree:
                    result = self.runner.invoke(app, ["cleanup", "--cache"])
        
        assert result.exit_code == 0
        assert "models preserved" in result.output
        mock_rmtree.assert_called_once_with(mock_item1)  # Only non-models removed
    
    @patch('ali.cli.system_cli.get_config')
    @patch('ali.cli.system_cli.common_setup')
    @patch('click.confirm')
    def test_cleanup_command_force(self, mock_confirm, mock_setup, mock_get_config):
        """Test cleanup command with force flag."""
        mock_config = Mock()
        mock_config.paths.logs_dir = Path("/test/logs")
        mock_get_config.return_value = mock_config
        mock_setup.return_value = Mock()
        
        with patch.object(Path, 'exists', return_value=True):
            with patch('shutil.rmtree'):
                with patch.object(Path, 'mkdir'):
                    result = self.runner.invoke(app, ["cleanup", "--logs", "--force"])
        
        assert result.exit_code == 0
        # confirm should not be called with --force
        mock_confirm.assert_not_called()


class TestSystemInfoIntegration:
    """Integration tests for system info functionality."""
    
    def test_get_system_info_real_call(self):
        """Test actual system info call returns valid data."""
        info = get_system_info()
        
        # Should return placeholder data for now
        assert info["memory"]["total_gb"] == 16.0
        assert info["cpu"]["brand"] == "Apple M1"
        assert info["gpu"]["available"] is True
        assert info["thermal_state"] == "nominal"
    
    def test_validate_benchmark_environment_real_call(self):
        """Test actual benchmark validation call."""
        result = validate_benchmark_environment()
        
        # Should return True for placeholder implementation
        assert result is True


class TestErrorHandling:
    """Test error handling in system CLI."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    @patch('ali.cli.system_cli.common_setup')
    def test_keyboard_interrupt_handling(self, mock_setup):
        """Test keyboard interrupt handling."""
        mock_setup.side_effect = KeyboardInterrupt()
        
        result = self.runner.invoke(app, ["info"])
        
        # Should exit with 130 (keyboard interrupt code)
        assert result.exit_code == 130
    
    @patch('ali.cli.system_cli.common_setup')
    def test_general_exception_handling(self, mock_setup):
        """Test general exception handling."""
        mock_base_cli = Mock()
        mock_base_cli.handle_error.side_effect = SystemExit(1)
        mock_setup.return_value = mock_base_cli
        
        with patch('ali.cli.system_cli.get_system_info', side_effect=Exception("Test error")):
            result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 1


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    @patch('ali.cli.system_cli.get_system_info')
    @patch('ali.cli.system_cli.common_setup')
    def test_info_command_missing_gpu(self, mock_setup, mock_get_info):
        """Test info command when GPU is not available."""
        mock_info = {
            "memory": {"total_gb": 8.0, "available_gb": 4.0, "used_percent": 50.0, "process_mb": 100.0},
            "cpu": {"brand": "Intel i5", "count": 4, "count_logical": 8, "usage_percent": 30.0},
            "gpu": {"available": False},
            "thermal_state": "fair"
        }
        
        mock_get_info.return_value = mock_info
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "Not detected or not available" in result.output
    
    @patch('ali.cli.system_cli.get_system_info')
    @patch('ali.cli.system_cli.common_setup')
    def test_info_command_no_thermal_state(self, mock_setup, mock_get_info):
        """Test info command when thermal state is not available."""
        mock_info = {
            "memory": {"total_gb": 8.0, "available_gb": 4.0, "used_percent": 50.0, "process_mb": 100.0},
            "cpu": {"brand": "Intel i5", "count": 4, "count_logical": 8, "usage_percent": 30.0},
            "gpu": {"available": True, "memory_mb": 4096, "memory_gb": 4.0, "cores": 16},
            "thermal_state": None
        }
        
        mock_get_info.return_value = mock_info
        mock_setup.return_value = Mock()
        
        result = self.runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        # Should not include thermal info section
        assert "Thermal" not in result.output