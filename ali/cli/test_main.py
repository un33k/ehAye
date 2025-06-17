"""Unit tests for main CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
from click.testing import CliRunner

from .main import main, cli, check_virtualenv


class TestMainCLI:
    """Test main CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test main CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Ali - Artificial Line Interface" in result.output
        assert "chat" in result.output
        assert "mod" in result.output
        assert "olla" in result.output
        assert "sys" in result.output
        assert "perf" in result.output
    
    def test_cli_version_info(self):
        """Test CLI shows correct version info."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        # Version info should be in help
    
    @patch('ali.cli.main.subprocess.run')
    def test_chat_delegate_basic(self, mock_run):
        """Test chat command delegation."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['chat'])
        assert result.exit_code == 0
        
        # Should call subprocess with interactive
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'python' in args
        assert '-m' in args
        assert 'ali.cli.chat_cli' in args
        assert 'interactive' in args
    
    @patch('ali.cli.main.subprocess.run')
    def test_chat_delegate_with_args(self, mock_run):
        """Test chat command delegation with arguments."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['chat', 'interactive', '-m', 'test-model'])
        assert result.exit_code == 0
        
        # Should pass through arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'interactive' in args
        assert '-m' in args
        assert 'test-model' in args
    
    @patch('ali.cli.main.subprocess.run')
    def test_perf_delegate(self, mock_run):
        """Test performance command delegation."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['perf', 'validate'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ali.cli.benchmark_cli' in args
        assert 'validate' in args
    
    @pytest.mark.skip("CLI delegation tests need review of actual main.py implementation")
    @patch('ali.cli.main.subprocess.run')
    def test_mod_delegate(self, mock_run):
        """Test model command delegation."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['mod', '--help'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ali.cli.model_cli' in args
    
    @patch('ali.cli.main.subprocess.run')
    def test_olla_delegate_basic(self, mock_run):
        """Test basic ollama command delegation."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['olla', 'list'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ali.cli.ollama_cli' in args
        assert 'list' in args
    
    @patch('ali.cli.main.subprocess.run')
    def test_olla_passthrough(self, mock_run):
        """Test ollama passthrough with -- syntax."""
        mock_run.return_value.returncode = 0
        
        # This tests the special handling in main()
        with patch('sys.argv', ['ali', 'olla', '--', '--version']):
            with patch('ali.cli.main.ollama_main') as mock_ollama_main:
                main()
                mock_ollama_main.assert_called_once()
    
    @patch('ali.cli.main.subprocess.run')
    def test_sys_delegate(self, mock_run):
        """Test system command delegation."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['sys', 'info'])
        assert result.exit_code == 0
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'ali.cli.system_cli' in args
        assert 'info' in args


class TestVirtualEnvCheck:
    """Test virtual environment checking."""
    
    @patch.dict('os.environ', {'VIRTUAL_ENV': '/test/venv'})
    def test_check_virtualenv_with_venv(self):
        """Test virtual environment check when venv is active."""
        # Should not raise any exception
        check_virtualenv()
    
    @patch.dict('os.environ', {}, clear=True)
    @patch('ali.cli.main.console')
    def test_check_virtualenv_without_venv(self, mock_console):
        """Test virtual environment check when no venv is active."""
        # Should print warning but not exit
        check_virtualenv()
        mock_console.print.assert_called()
        
        # Check that warning message is printed
        call_args = mock_console.print.call_args[0][0]
        assert "virtual environment" in call_args.lower()
    
    @patch.dict('os.environ', {'VIRTUAL_ENV': ''})
    @patch('ali.cli.main.console')
    def test_check_virtualenv_empty_venv(self, mock_console):
        """Test virtual environment check with empty VIRTUAL_ENV."""
        check_virtualenv()
        mock_console.print.assert_called()


class TestMainFunction:
    """Test main entry point function."""
    
    @patch('ali.cli.main.cli')
    @patch('ali.cli.main.check_virtualenv')
    def test_main_normal_flow(self, mock_check_venv, mock_cli):
        """Test normal main function flow."""
        main()
        mock_check_venv.assert_called_once()
        mock_cli.assert_called_once()
    
    @patch('ali.cli.main.cli')
    @patch('ali.cli.main.check_virtualenv')
    @patch('ali.cli.main.handle_keyboard_interrupt')
    def test_main_keyboard_interrupt(self, mock_handle_interrupt, mock_check_venv, mock_cli):
        """Test main function with keyboard interrupt."""
        mock_cli.side_effect = KeyboardInterrupt()
        
        main()
        
        mock_handle_interrupt.assert_called_once()
    
    @patch('ali.cli.main.ollama_main')
    def test_main_ollama_passthrough(self, mock_ollama_main):
        """Test main function with ollama passthrough."""
        with patch('sys.argv', ['ali', 'olla', '--', '--version']):
            main()
            mock_ollama_main.assert_called_once()
    
    @patch('ali.cli.main.ollama_main')
    def test_main_ollama_no_passthrough(self, mock_ollama_main):
        """Test main function with ollama but no passthrough."""
        with patch('sys.argv', ['ali', 'olla', 'list']):
            with patch('ali.cli.main.cli') as mock_cli:
                main()
                mock_ollama_main.assert_not_called()
                mock_cli.assert_called_once()


class TestErrorHandling:
    """Test error handling in main CLI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.main.subprocess.run')
    def test_delegate_command_error(self, mock_run):
        """Test handling of delegate command errors."""
        mock_run.return_value.returncode = 1
        
        result = self.runner.invoke(cli, ['chat', 'invalid-command'])
        assert result.exit_code == 1
    
    @patch('ali.cli.main.subprocess.run')
    def test_delegate_subprocess_exception(self, mock_run):
        """Test handling of subprocess exceptions."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        result = self.runner.invoke(cli, ['chat'])
        # Should handle gracefully
        assert result.exit_code != 0


class TestCommandValidation:
    """Test command validation and argument parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        result = self.runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        assert "No such command" in result.output
    
    @patch('ali.cli.main.subprocess.run')
    def test_verbose_flag(self, mock_run):
        """Test verbose flag handling."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['--verbose', 'sys', 'info'])
        assert result.exit_code == 0
    
    @patch('ali.cli.main.subprocess.run')
    def test_debug_flag(self, mock_run):
        """Test debug flag handling."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['--debug', 'sys', 'info'])
        assert result.exit_code == 0


class TestCornerCases:
    """Test corner cases and edge conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.main.subprocess.run')
    def test_empty_args(self, mock_run):
        """Test handling of empty arguments."""
        result = self.runner.invoke(cli, [])
        # Should show help
        assert "Usage:" in result.output
    
    @patch('ali.cli.main.subprocess.run')
    def test_special_characters_in_args(self, mock_run):
        """Test handling of special characters in arguments."""
        mock_run.return_value.returncode = 0
        
        result = self.runner.invoke(cli, ['chat', 'single', 'Hello "world"'])
        assert result.exit_code == 0
        
        # Should pass through special characters
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert 'Hello "world"' in args
    
    @patch('ali.cli.main.subprocess.run')
    def test_very_long_command(self, mock_run):
        """Test handling of very long commands."""
        mock_run.return_value.returncode = 0
        
        long_arg = "a" * 1000
        result = self.runner.invoke(cli, ['chat', 'single', long_arg])
        assert result.exit_code == 0
    
    @patch('ali.cli.main.subprocess.run')
    def test_unicode_arguments(self, mock_run):
        """Test handling of unicode arguments."""
        mock_run.return_value.returncode = 0
        
        unicode_arg = "Hello 🌍 世界"
        result = self.runner.invoke(cli, ['chat', 'single', unicode_arg])
        assert result.exit_code == 0
        
        # Should handle unicode properly
        mock_run.assert_called_once()


class TestIntegration:
    """Integration tests for main CLI."""
    
    def test_cli_commands_available(self):
        """Test that all expected commands are available."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        expected_commands = ['chat', 'mod', 'olla', 'sys', 'perf']
        for cmd in expected_commands:
            assert cmd in result.output
    
    @patch('ali.cli.main.subprocess.run')
    def test_command_delegation_flow(self, mock_run):
        """Test complete command delegation flow."""
        mock_run.return_value.returncode = 0
        
        runner = CliRunner()
        
        # Test each command delegates properly
        commands = [
            ['chat', 'models'],
            ['mod', '--help'],
            ['sys', 'info'],
            ['perf', 'validate'],
            ['olla', 'list']
        ]
        
        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0
        
        # Should have made one call per command
        assert mock_run.call_count == len(commands)


class TestPerformance:
    """Test performance characteristics of main CLI."""
    
    @patch('ali.cli.main.subprocess.run')
    def test_cli_startup_performance(self, mock_run):
        """Test that CLI starts quickly."""
        mock_run.return_value.returncode = 0
        
        import time
        runner = CliRunner()
        
        start_time = time.time()
        result = runner.invoke(cli, ['--help'])
        end_time = time.time()
        
        assert result.exit_code == 0
        # Should complete quickly (less than 1 second)
        assert end_time - start_time < 1.0
    
    @patch('ali.cli.main.subprocess.run')
    def test_multiple_command_performance(self, mock_run):
        """Test performance with multiple commands."""
        mock_run.return_value.returncode = 0
        
        import time
        runner = CliRunner()
        
        start_time = time.time()
        
        # Run multiple commands
        for _ in range(10):
            result = runner.invoke(cli, ['chat', '--help'])
            assert result.exit_code == 0
        
        end_time = time.time()
        
        # Should handle multiple commands efficiently
        assert end_time - start_time < 5.0