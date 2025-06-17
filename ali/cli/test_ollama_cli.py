"""Unit tests for Ollama CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
from click.testing import CliRunner

from .ollama_cli import main, cli, check_ollama


class TestOllamaCLI:
    """Test Ollama CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test Ollama CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Ollama operations" in result.output
        assert "pull" in result.output
        assert "run" in result.output
        assert "list" in result.output
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_pull_command(self, mock_run):
        """Test ollama pull command."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "pulling model..."
        
        result = self.runner.invoke(cli, ['pull', 'test-model'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'pull' in args
        assert 'test-model' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_list_command(self, mock_run):
        """Test ollama list command."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "NAME\tID\tSIZE\ntest-model\t123\t1GB"
        
        result = self.runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'list' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_run_command(self, mock_run):
        """Test ollama run command."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['run', 'test-model'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'run' in args
        assert 'test-model' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_remove_command(self, mock_run):
        """Test ollama remove command."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['rm', 'test-model'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'rm' in args
        assert 'test-model' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_start_command(self, mock_run):
        """Test ollama start command."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['start'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'start' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_stop_command(self, mock_run):
        """Test ollama stop command."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['stop'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'stop' in args


class TestOllamaValidation:
    """Test Ollama validation functionality."""
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_check_ollama_success(self, mock_run):
        """Test successful Ollama check."""
        mock_run.return_value.returncode = 0
        
        result = check_ollama()
        assert result is True
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'list' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_check_ollama_not_found(self, mock_run):
        """Test Ollama check when ollama not found."""
        mock_run.side_effect = FileNotFoundError("ollama command not found")
        
        result = check_ollama()
        assert result is False
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_check_ollama_error(self, mock_run):
        """Test Ollama check with error."""
        mock_run.return_value.returncode = 1
        
        result = check_ollama()
        assert result is False


class TestOllamaPassthrough:
    """Test Ollama command passthrough functionality."""
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_passthrough_simple_command(self, mock_run):
        """Test passthrough with simple command."""
        mock_run.return_value.returncode = 0
        
        # Simulate main() with passthrough args
        with patch('sys.argv', ['ali', 'olla', '--', '--version']):
            main()
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert '--version' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_passthrough_complex_command(self, mock_run):
        """Test passthrough with complex command."""
        mock_run.return_value.returncode = 0
        
        with patch('sys.argv', ['ali', 'olla', '--', 'create', 'mymodel', '-f', 'Modelfile']):
            main()
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ollama' in args
        assert 'create' in args
        assert 'mymodel' in args
        assert '-f' in args
        assert 'Modelfile' in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_passthrough_with_quotes(self, mock_run):
        """Test passthrough with quoted arguments."""
        mock_run.return_value.returncode = 0
        
        with patch('sys.argv', ['ali', 'olla', '--', 'run', 'model', 'Hello "world"']):
            main()
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'Hello "world"' in args


class TestErrorHandling:
    """Test error handling in Ollama CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_command_error(self, mock_run):
        """Test handling of command errors."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "error: model not found"
        
        result = self.runner.invoke(cli, ['pull', 'nonexistent-model'])
        assert result.exit_code == 1
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_subprocess_exception(self, mock_run):
        """Test handling of subprocess exceptions."""
        mock_run.side_effect = FileNotFoundError("ollama command not found")
        
        result = self.runner.invoke(cli, ['list'])
        assert result.exit_code != 0
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_keyboard_interrupt(self, mock_run):
        """Test handling of keyboard interrupt."""
        mock_run.side_effect = KeyboardInterrupt()
        
        with patch('ali.cli.ollama_cli.handle_keyboard_interrupt') as mock_handle:
            result = self.runner.invoke(cli, ['pull', 'large-model'])
            # Should handle gracefully
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_timeout_handling(self, mock_run):
        """Test handling of command timeouts."""
        mock_run.side_effect = subprocess.TimeoutExpired(['ollama'], 30)
        
        result = self.runner.invoke(cli, ['pull', 'large-model'])
        # Should handle timeout gracefully


class TestArgumentParsing:
    """Test argument parsing and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_missing_model_argument(self):
        """Test handling of missing model argument."""
        result = self.runner.invoke(cli, ['pull'])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Usage:" in result.output
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_extra_arguments(self, mock_run):
        """Test handling of extra arguments."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['pull', 'model', '--extra', 'arg'])
        # Should pass through extra arguments
        mock_run.assert_called_once()


class TestSpecialCases:
    """Test special cases and edge conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_empty_model_name(self, mock_run):
        """Test handling of empty model name."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['pull', ''])
        # Should handle gracefully or show error
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_unicode_model_name(self, mock_run):
        """Test handling of unicode in model names."""
        mock_run.return_value.returncode = 0
        
        unicode_name = "模型-🤖"
        result = self.runner.invoke(cli, ['pull', unicode_name])
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert unicode_name in args
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_very_long_model_name(self, mock_run):
        """Test handling of very long model names."""
        mock_run.return_value.returncode = 0
        
        long_name = "a" * 1000
        result = self.runner.invoke(cli, ['pull', long_name])
        
        mock_run.assert_called_once()
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_special_characters_in_model(self, mock_run):
        """Test handling of special characters in model names."""
        mock_run.return_value.returncode = 0
        
        special_name = "model-with-special@chars:latest"
        result = self.runner.invoke(cli, ['pull', special_name])
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert special_name in args


class TestPerformance:
    """Test performance characteristics."""
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_command_performance(self, mock_run):
        """Test that commands execute quickly."""
        mock_run.return_value.returncode = 0
        
        import time
        runner = CliRunner()
        
        start_time = time.time()
        result = runner.invoke(cli, ['list'])
        end_time = time.time()
        
        assert result.exit_code == 0
        # Should complete quickly (overhead should be minimal)
        assert end_time - start_time < 1.0
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_multiple_commands_performance(self, mock_run):
        """Test performance with multiple commands."""
        mock_run.return_value.returncode = 0
        
        import time
        runner = CliRunner()
        
        start_time = time.time()
        
        for _ in range(5):
            result = runner.invoke(cli, ['list'])
            assert result.exit_code == 0
        
        end_time = time.time()
        
        # Should handle multiple commands efficiently
        assert end_time - start_time < 3.0


class TestMainFunction:
    """Test main function behavior."""
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_main_with_regular_args(self, mock_run):
        """Test main function with regular arguments."""
        mock_run.return_value.returncode = 0
        
        with patch('sys.argv', ['ali', 'olla', 'list']):
            with patch('ali.cli.ollama_cli.cli') as mock_cli:
                main()
                mock_cli.assert_called_once()
    
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_main_with_passthrough(self, mock_run):
        """Test main function with passthrough arguments."""
        mock_run.return_value.returncode = 0
        
        with patch('sys.argv', ['ali', 'olla', '--', '--version']):
            main()
            
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert 'ollama' in args
            assert '--version' in args
    
    @patch('ali.cli.ollama_cli.handle_keyboard_interrupt')
    def test_main_keyboard_interrupt(self, mock_handle):
        """Test main function with keyboard interrupt."""
        with patch('ali.cli.ollama_cli.cli') as mock_cli:
            mock_cli.side_effect = KeyboardInterrupt()
            
            main()
            mock_handle.assert_called_once()


class TestIntegration:
    """Integration tests for Ollama CLI."""
    
    def test_cli_structure(self):
        """Test CLI command structure."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        expected_commands = ['pull', 'run', 'list', 'rm', 'start', 'stop']
        for cmd in expected_commands:
            assert cmd in result.output
    
    @patch('ali.cli.ollama_cli.check_ollama')
    @patch('ali.cli.ollama_cli.subprocess.run')
    def test_validation_integration(self, mock_run, mock_check):
        """Test integration with validation."""
        mock_check.return_value = True
        mock_run.return_value.returncode = 0
        
        runner = CliRunner()
        result = runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0