"""Unit tests for CLI base functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import click
from click.testing import CliRunner

from .base import (
    BaseCLI, 
    common_setup, 
    handle_keyboard_interrupt, 
    confirm_action, 
    show_success, 
    show_warning, 
    show_error, 
    show_info
)


class TestBaseCLI:
    """Test BaseCLI class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cli = BaseCLI("test_app")
        
    def test_init(self):
        """Test BaseCLI initialization."""
        assert self.cli.app_name == "test_app"
        assert self.cli.config is None
        
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        with patch('ali.cli.base.ehaye_logger') as mock_logger:
            self.cli.setup_logging()
            mock_logger.setup.assert_called_once_with(
                level="INFO", 
                log_file=None, 
                enable_rich=True
            )
    
    def test_setup_logging_verbose(self):
        """Test setup_logging with verbose flag."""
        with patch('ali.cli.base.ehaye_logger') as mock_logger:
            self.cli.setup_logging(verbose=True)
            mock_logger.setup.assert_called_once_with(
                level="DEBUG", 
                log_file=None, 
                enable_rich=True
            )
    
    def test_setup_logging_quiet(self):
        """Test setup_logging with quiet flag."""
        with patch('ali.cli.base.ehaye_logger') as mock_logger:
            self.cli.setup_logging(quiet=True)
            mock_logger.setup.assert_called_once_with(
                level="ERROR", 
                log_file=None, 
                enable_rich=False
            )
            
    def test_setup_logging_with_config(self):
        """Test setup_logging with config containing log path."""
        mock_config = Mock()
        mock_config.paths.logs_dir = Path("/test/logs")
        self.cli.config = mock_config
        
        with patch('ali.cli.base.ehaye_logger') as mock_logger:
            self.cli.setup_logging()
            expected_log_file = Path("/test/logs/test_app.log")
            mock_logger.setup.assert_called_once_with(
                level="INFO", 
                log_file=expected_log_file, 
                enable_rich=True
            )
    
    @patch('ali.cli.base.load_config')
    def test_load_configuration_success(self, mock_load_config):
        """Test successful configuration loading."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        self.cli.load_configuration()
        
        assert self.cli.config == mock_config
        mock_config.setup_environment.assert_called_once()
    
    @patch('ali.cli.base.load_config')
    def test_load_configuration_failure(self, mock_load_config):
        """Test configuration loading failure."""
        mock_load_config.side_effect = Exception("Config error")
        
        with pytest.raises(click.ClickException):
            self.cli.load_configuration()
    
    def test_validate_environment_success(self):
        """Test successful environment validation."""
        with patch.dict('os.environ', {'VIRTUAL_ENV': '/test/venv'}):
            with patch('sys.version_info', (3, 11, 0)):
                # Should not raise exception
                self.cli.validate_environment()
    
    def test_validate_environment_skip_venv(self):
        """Test environment validation with skip_venv=True."""
        with patch('sys.version_info', (3, 11, 0)):
            # Should not raise exception even without VIRTUAL_ENV
            self.cli.validate_environment(skip_venv=True)
    
    def test_validate_environment_no_venv(self):
        """Test environment validation failure - no virtual env."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(click.ClickException):
                self.cli.validate_environment()
    
    def test_validate_environment_old_python(self):
        """Test environment validation failure - old Python version."""
        with patch.dict('os.environ', {'VIRTUAL_ENV': '/test/venv'}):
            with patch('sys.version_info', (3, 9, 0)):
                with pytest.raises(click.ClickException):
                    self.cli.validate_environment()
    
    def test_handle_error_ehaye_error(self):
        """Test error handling for EhAyeError."""
        from ali.exceptions import EhAyeError
        
        error = EhAyeError("Test error", "TEST_001")
        
        with pytest.raises(click.ClickException):
            self.cli.handle_error(error)
    
    def test_handle_error_generic_error(self):
        """Test error handling for generic errors."""
        error = ValueError("Generic error")
        
        with pytest.raises(click.ClickException):
            self.cli.handle_error(error)


class TestCommonFunctions:
    """Test common CLI functions."""
    
    @patch('ali.cli.base.BaseCLI')
    def test_common_setup_default(self, mock_base_cli):
        """Test common_setup with default parameters."""
        mock_cli = Mock()
        mock_base_cli.return_value = mock_cli
        
        result = common_setup()
        
        assert result == mock_cli
        mock_cli.setup_logging.assert_called_once_with(False, False)
        mock_cli.load_configuration.assert_called_once_with(None)
        mock_cli.validate_environment.assert_called_once_with(False)
    
    @patch('ali.cli.base.BaseCLI')
    def test_common_setup_with_context(self, mock_base_cli):
        """Test common_setup with click context."""
        mock_cli = Mock()
        mock_base_cli.return_value = mock_cli
        mock_ctx = Mock()
        mock_ctx.info_name = "test_command"
        
        result = common_setup(mock_ctx, verbose=True, quiet=False)
        
        mock_base_cli.assert_called_once_with("test_command")
        mock_cli.setup_logging.assert_called_once_with(True, False)
    
    def test_handle_keyboard_interrupt(self):
        """Test keyboard interrupt handler."""
        with pytest.raises(SystemExit) as exc_info:
            handle_keyboard_interrupt()
        assert exc_info.value.code == 130
    
    @patch('click.confirm')
    def test_confirm_action(self, mock_confirm):
        """Test confirm_action function."""
        mock_confirm.return_value = True
        
        result = confirm_action("Test message", default=False)
        
        assert result is True
        mock_confirm.assert_called_once_with("Test message", default=False)


class TestDisplayFunctions:
    """Test CLI display functions."""
    
    @patch('ali.cli.base.console')
    def test_show_success(self, mock_console):
        """Test show_success function."""
        show_success("Test success")
        mock_console.print.assert_called_once_with("[green]✅ Test success[/green]")
    
    @patch('ali.cli.base.console')
    def test_show_warning(self, mock_console):
        """Test show_warning function."""
        show_warning("Test warning")
        mock_console.print.assert_called_once_with("[yellow]⚠️  Test warning[/yellow]")
    
    @patch('ali.cli.base.console')
    def test_show_error(self, mock_console):
        """Test show_error function."""
        show_error("Test error")
        mock_console.print.assert_called_once_with("[red]❌ Test error[/red]")
    
    @patch('ali.cli.base.console')
    def test_show_info(self, mock_console):
        """Test show_info function."""
        show_info("Test info")
        mock_console.print.assert_called_once_with("[blue]ℹ️  Test info[/blue]")


class TestIntegration:
    """Integration tests for base CLI functionality."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_click_integration(self):
        """Test Click integration with base CLI patterns."""
        @click.command()
        @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
        @click.pass_context
        def test_command(ctx, verbose):
            """Test command."""
            base_cli = BaseCLI("test")
            base_cli.setup_logging(verbose=verbose)
            click.echo("Success")
        
        result = self.runner.invoke(test_command, ["--verbose"])
        assert result.exit_code == 0
        assert "Success" in result.output