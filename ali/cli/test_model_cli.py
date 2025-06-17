"""Unit tests for model CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from io import StringIO
import click

from .model_cli import (
    main, setup_logging, get_command_prefix, show_help,
    handle_list, handle_search, handle_download, handle_remove, handle_info,
    select_model_for_download, select_installed_model
)


class TestSetupLogging:
    """Test logging setup functionality."""
    
    @patch('ali.cli.model_cli.ehaye_logger')
    def test_setup_logging_debug(self, mock_logger):
        """Test logging setup with debug level."""
        setup_logging(verbose=False, debug=True)
        mock_logger.setup.assert_called_once_with(level="DEBUG", enable_rich=True)
    
    @patch('ali.cli.model_cli.ehaye_logger')
    def test_setup_logging_verbose(self, mock_logger):
        """Test logging setup with verbose level."""
        setup_logging(verbose=True, debug=False)
        mock_logger.setup.assert_called_once_with(level="INFO", enable_rich=True)
    
    @patch('ali.cli.model_cli.ehaye_logger')
    def test_setup_logging_quiet(self, mock_logger):
        """Test logging setup with quiet level."""
        setup_logging(verbose=False, debug=False)
        mock_logger.setup.assert_called_once_with(level="CRITICAL", enable_rich=True)


class TestCommandPrefix:
    """Test command prefix functionality."""
    
    @patch('ali.cli.model_cli.get_config')
    def test_get_command_prefix_success(self, mock_get_config):
        """Test getting command prefix from config."""
        mock_config = Mock()
        mock_config.cli.main_command = "ehaye"
        mock_config.cli.model_command = "models"
        mock_get_config.return_value = mock_config
        
        result = get_command_prefix()
        assert result == "ehaye models"
    
    @patch('ali.cli.model_cli.get_config')
    def test_get_command_prefix_fallback(self, mock_get_config):
        """Test command prefix fallback when config fails."""
        mock_get_config.side_effect = Exception("Config error")
        
        result = get_command_prefix()
        assert result == "ali mod"


class TestHelp:
    """Test help functionality."""
    
    @patch('ali.cli.model_cli.get_command_prefix')
    @patch('ali.cli.model_cli.console')
    def test_show_help(self, mock_console, mock_get_prefix):
        """Test showing help message."""
        mock_get_prefix.return_value = "ali mod"
        
        show_help()
        
        # Verify help content was printed
        assert mock_console.print.call_count > 10
        # Check that help contains expected sections
        calls = [call[0][0] for call in mock_console.print.call_args_list]
        help_text = " ".join(str(call) for call in calls)
        
        assert "ehAye Models CLI" in help_text
        assert "--list" in help_text
        assert "--search" in help_text
        assert "--download" in help_text


class TestMainFunction:
    """Test main function argument parsing and execution."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.original_argv = sys.argv.copy()
    
    def teardown_method(self):
        """Restore original argv."""
        sys.argv = self.original_argv
    
    @patch('ali.cli.model_cli.show_help')
    def test_main_help_flag(self, mock_show_help):
        """Test main with help flag."""
        sys.argv = ['model_cli.py', '--help']
        
        main()
        
        mock_show_help.assert_called_once()
    
    @patch('ali.cli.model_cli.show_help')
    def test_main_no_actions(self, mock_show_help):
        """Test main with no action flags."""
        sys.argv = ['model_cli.py']
        
        main()
        
        mock_show_help.assert_called_once()
    
    @patch('ali.cli.model_cli.show_error')
    def test_main_multiple_actions(self, mock_show_error):
        """Test main with multiple action flags."""
        sys.argv = ['model_cli.py', '--list', '--search']
        
        with patch('ali.cli.model_cli.setup_logging'):
            main()
        
        mock_show_error.assert_called_once()
        assert "only one action" in mock_show_error.call_args[0][0]
    
    @patch('ali.cli.model_cli.handle_list')
    @patch('ali.cli.model_cli.setup_logging')
    @patch('ali.cli.model_cli.get_logger')
    @patch('ali.cli.model_cli.common_setup')
    def test_main_list_action(self, mock_setup, mock_logger, mock_logging, mock_handle):
        """Test main with list action."""
        sys.argv = ['model_cli.py', '--list']
        
        mock_logger.return_value = Mock()
        
        main()
        
        mock_handle.assert_called_once()
    
    @patch('ali.cli.model_cli.handle_search')
    @patch('ali.cli.model_cli.setup_logging')
    @patch('ali.cli.model_cli.get_logger')
    @patch('ali.cli.model_cli.common_setup')
    def test_main_search_with_query(self, mock_setup, mock_logger, mock_logging, mock_handle):
        """Test main with search action and query."""
        sys.argv = ['model_cli.py', '--search', '--query', 'phi']
        
        mock_logger.return_value = Mock()
        
        main()
        
        mock_handle.assert_called_once()
        # Check that params contain the query
        call_args = mock_handle.call_args[0]
        params = call_args[2]  # Third argument is params
        assert params['query'] == 'phi'
    
    @patch('ali.cli.model_cli.handle_download')
    @patch('ali.cli.model_cli.setup_logging')
    @patch('ali.cli.model_cli.get_logger')
    @patch('ali.cli.model_cli.common_setup')
    def test_main_download_with_model(self, mock_setup, mock_logger, mock_logging, mock_handle):
        """Test main with download action and model."""
        sys.argv = ['model_cli.py', '--download', '--model', 'phi3']
        
        mock_logger.return_value = Mock()
        
        main()
        
        mock_handle.assert_called_once()
        call_args = mock_handle.call_args[0]
        params = call_args[1]  # Second argument is params
        assert params['model'] == 'phi3'
    
    @patch('ali.cli.model_cli.handle_keyboard_interrupt')
    @patch('ali.cli.model_cli.setup_logging')
    def test_main_keyboard_interrupt(self, mock_logging, mock_handle):
        """Test main with keyboard interrupt."""
        sys.argv = ['model_cli.py', '--list']
        
        with patch('ali.cli.model_cli.get_logger') as mock_logger:
            mock_logger.side_effect = KeyboardInterrupt()
            
            main()
            
            mock_handle.assert_called_once()


class TestHandleList:
    """Test list operation handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_manager = Mock()
        self.params = {'provider': 'ollama', 'verbose': False}
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_list_success(self, mock_logger, mock_console):
        """Test successful model listing."""
        # Mock models
        mock_model = Mock()
        mock_model.name = "Test Model"
        mock_model.id = "test-model"
        mock_model.size = "3.8GB"
        mock_model.family = "test"
        self.mock_backend.list_models.return_value = [mock_model]
        
        handle_list(self.mock_backend, self.mock_manager, self.params)
        
        self.mock_backend.list_models.assert_called_once()
        # Verify console output
        assert mock_console.print.call_count > 0
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_list_with_filters(self, mock_logger, mock_console):
        """Test model listing with filters."""
        # Mock models
        mock_model1 = Mock()
        mock_model1.name = "Phi Model"
        mock_model1.id = "phi3"
        mock_model1.size = "3.8GB"
        mock_model1.family = "phi"
        
        mock_model2 = Mock()
        mock_model2.name = "Llama Model"
        mock_model2.id = "llama3"
        mock_model2.size = "8GB"
        mock_model2.family = "llama"
        
        self.mock_backend.list_models.return_value = [mock_model1, mock_model2]
        
        # Test with query filter
        params = {**self.params, 'query': 'phi'}
        handle_list(self.mock_backend, self.mock_manager, params)
        
        # Verify filtered output
        assert mock_console.print.call_count > 0
    
    @patch('ali.cli.model_cli.show_error')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_list_no_models(self, mock_logger, mock_show_error):
        """Test listing when no models found."""
        self.mock_backend.list_models.return_value = []
        
        handle_list(self.mock_backend, self.mock_manager, self.params)
        
        mock_show_error.assert_called_once_with("No models found")
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_list_all_providers(self, mock_logger, mock_console):
        """Test listing models from all providers."""
        params = {**self.params, 'provider': 'all'}
        
        # Mock manager response
        mock_model = Mock()
        mock_model.name = "Test Model"
        mock_model.description = None
        self.mock_manager.list_all_models.return_value = {
            'ollama': [mock_model]
        }
        
        handle_list(self.mock_backend, self.mock_manager, params)
        
        self.mock_manager.list_all_models.assert_called_once()


class TestHandleSearch:
    """Test search operation handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_manager = Mock()
        self.params = {'provider': 'ollama', 'verbose': False}
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_search_success(self, mock_logger, mock_console):
        """Test successful model search."""
        # Mock models
        mock_model = Mock()
        mock_model.name = "Available Model"
        mock_model.id = "available-model"
        mock_model.size = "3.8GB"
        mock_model.family = "test"
        self.mock_backend.search_models.return_value = [mock_model]
        
        handle_search(self.mock_backend, self.mock_manager, self.params)
        
        self.mock_backend.search_models.assert_called_once_with(None)
        assert mock_console.print.call_count > 0
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_search_with_query(self, mock_logger, mock_console):
        """Test search with specific query."""
        params = {**self.params, 'query': 'phi'}
        
        mock_model = Mock()
        mock_model.name = "Phi Model"
        mock_model.id = "phi3"
        mock_model.size = "3.8GB"
        self.mock_backend.search_models.return_value = [mock_model]
        
        handle_search(self.mock_backend, self.mock_manager, params)
        
        self.mock_backend.search_models.assert_called_once_with('phi')
    
    @patch('ali.cli.model_cli.show_error')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_search_no_results(self, mock_logger, mock_show_error):
        """Test search with no results."""
        self.mock_backend.search_models.return_value = []
        
        handle_search(self.mock_backend, self.mock_manager, self.params)
        
        mock_show_error.assert_called_once_with("No models found")


class TestHandleDownload:
    """Test download operation handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.params = {'model': 'test-model', 'force': False, 'verbose': False}
    
    @patch('ali.cli.model_cli.show_success')
    @patch('ali.cli.model_cli.show_info')
    @patch('ali.cli.model_cli.get_logger')
    @patch('ali.cli.model_cli.console')
    def test_handle_download_success(self, mock_console, mock_logger, mock_show_info, mock_show_success):
        """Test successful model download."""
        # Mock backend methods
        self.mock_backend.list_models.return_value = []  # Not already installed
        
        mock_model_info = Mock()
        mock_model_info.name = "Test Model"
        mock_model_info.id = "test-model"
        mock_model_info.size = "3.8GB"
        self.mock_backend.download_model.return_value = mock_model_info
        
        handle_download(self.mock_backend, self.params)
        
        self.mock_backend.download_model.assert_called_once()
        mock_show_success.assert_called_once()
    
    @patch('ali.cli.model_cli.select_model_for_download')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_download_interactive(self, mock_logger, mock_select):
        """Test interactive model download."""
        params = {**self.params, 'interactive': True}
        mock_select.return_value = 'selected-model'
        
        # Mock backend methods
        self.mock_backend.list_models.return_value = []
        mock_model_info = Mock()
        mock_model_info.name = "Selected Model"
        self.mock_backend.download_model.return_value = mock_model_info
        
        with patch('ali.cli.model_cli.show_success'):
            handle_download(self.mock_backend, params)
        
        mock_select.assert_called_once_with(self.mock_backend)
    
    @patch('ali.cli.model_cli.show_error')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_download_no_model(self, mock_logger, mock_show_error):
        """Test download without specifying model."""
        params = {'force': False, 'verbose': False}  # No model specified
        
        handle_download(self.mock_backend, params)
        
        mock_show_error.assert_called_once()
        assert "specify a model ID" in mock_show_error.call_args[0][0]
    
    @patch('ali.cli.model_cli.confirm_action')
    @patch('ali.cli.model_cli.show_info')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_download_already_installed(self, mock_logger, mock_show_info, mock_confirm):
        """Test download when model already installed."""
        # Mock already installed model
        mock_installed = Mock()
        mock_installed.id = "test-model"
        self.mock_backend.list_models.return_value = [mock_installed]
        
        mock_confirm.return_value = False  # User cancels
        
        handle_download(self.mock_backend, self.params)
        
        mock_show_info.assert_called_once()
        assert "already installed" in mock_show_info.call_args[0][0]
        mock_confirm.assert_called_once()


class TestHandleRemove:
    """Test remove operation handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.params = {'model': 'test-model', 'force': False}
    
    @patch('ali.cli.model_cli.confirm_action')
    @patch('ali.cli.model_cli.show_success')
    @patch('ali.cli.model_cli.show_info')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_remove_success(self, mock_logger, mock_show_info, mock_show_success, mock_confirm):
        """Test successful model removal."""
        mock_confirm.return_value = True
        self.mock_backend.remove_model.return_value = True
        
        handle_remove(self.mock_backend, self.params)
        
        mock_confirm.assert_called_once()
        self.mock_backend.remove_model.assert_called_once_with('test-model')
        mock_show_success.assert_called_once()
    
    @patch('ali.cli.model_cli.confirm_action')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_remove_cancelled(self, mock_logger, mock_confirm):
        """Test model removal when user cancels."""
        mock_confirm.return_value = False
        
        handle_remove(self.mock_backend, self.params)
        
        mock_confirm.assert_called_once()
        self.mock_backend.remove_model.assert_not_called()
    
    @patch('ali.cli.model_cli.show_success')
    @patch('ali.cli.model_cli.show_info')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_remove_force(self, mock_logger, mock_show_info, mock_show_success):
        """Test forced model removal."""
        params = {**self.params, 'force': True}
        self.mock_backend.remove_model.return_value = True
        
        handle_remove(self.mock_backend, params)
        
        self.mock_backend.remove_model.assert_called_once_with('test-model')
        mock_show_success.assert_called_once()


class TestHandleInfo:
    """Test info operation handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.params = {'model': 'test-model'}
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_info_success(self, mock_logger, mock_console):
        """Test successful model info display."""
        # Mock model info
        mock_model_info = Mock()
        mock_model_info.name = "Test Model"
        mock_model_info.id = "test-model"
        mock_model_info.family = "test"
        mock_model_info.size = "3.8GB"
        mock_model_info.format = "gguf"
        mock_model_info.description = "Test model description"
        
        self.mock_backend.get_model_info.return_value = mock_model_info
        
        handle_info(self.mock_backend, self.params)
        
        self.mock_backend.get_model_info.assert_called_once_with('test-model')
        assert mock_console.print.call_count > 0
    
    @patch('ali.cli.model_cli.show_error')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_info_not_found(self, mock_logger, mock_show_error):
        """Test info when model not found."""
        self.mock_backend.get_model_info.return_value = None
        
        handle_info(self.mock_backend, self.params)
        
        mock_show_error.assert_called_once()
        assert "not found" in mock_show_error.call_args[0][0]


class TestInteractiveFunctions:
    """Test interactive selection functions."""
    
    @patch('ali.cli.model_cli.console')
    @patch('click.prompt')
    def test_select_model_for_download_success(self, mock_prompt, mock_console):
        """Test successful interactive model selection for download."""
        mock_backend = Mock()
        
        # Mock available models
        mock_model = Mock()
        mock_model.name = "Available Model"
        mock_model.id = "available-model"
        mock_model.size = "3.8GB"
        mock_backend.search_models.return_value = [mock_model]
        
        mock_prompt.return_value = "1"
        
        result = select_model_for_download(mock_backend)
        
        assert result == "available-model"
        mock_prompt.assert_called_once()
    
    @patch('ali.cli.model_cli.show_error')
    def test_select_model_for_download_no_models(self, mock_show_error):
        """Test selection when no models available."""
        mock_backend = Mock()
        mock_backend.search_models.return_value = []
        
        result = select_model_for_download(mock_backend)
        
        assert result is None
        mock_show_error.assert_called_once()
    
    @patch('ali.cli.model_cli.console')
    @patch('click.prompt')
    def test_select_model_for_download_quit(self, mock_prompt, mock_console):
        """Test quitting model selection."""
        mock_backend = Mock()
        mock_model = Mock()
        mock_model.name = "Test Model"
        mock_backend.search_models.return_value = [mock_model]
        
        mock_prompt.return_value = "q"
        
        result = select_model_for_download(mock_backend)
        
        assert result is None
    
    @patch('ali.cli.model_cli.console')
    @patch('click.prompt')
    def test_select_installed_model_success(self, mock_prompt, mock_console):
        """Test successful selection of installed model."""
        mock_backend = Mock()
        
        # Mock installed models
        mock_model = Mock()
        mock_model.name = "Installed Model"
        mock_model.id = "installed-model"
        mock_model.size = "3.8GB"
        mock_backend.list_models.return_value = [mock_model]
        
        mock_prompt.return_value = "1"
        
        result = select_installed_model(mock_backend)
        
        assert result == "installed-model"
    
    @patch('ali.cli.model_cli.show_error')
    def test_select_installed_model_no_models(self, mock_show_error):
        """Test selection when no models installed."""
        mock_backend = Mock()
        mock_backend.list_models.return_value = []
        
        result = select_installed_model(mock_backend)
        
        assert result is None
        mock_show_error.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('ali.cli.model_cli.show_error')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_list_exception(self, mock_logger, mock_show_error):
        """Test handling exception in list operation."""
        mock_backend = Mock()
        mock_backend.list_models.side_effect = Exception("Backend error")
        mock_manager = Mock()
        params = {'provider': 'ollama'}
        
        handle_list(mock_backend, mock_manager, params)
        
        mock_show_error.assert_called_once()
        assert "Failed to list models" in mock_show_error.call_args[0][0]
    
    @patch('ali.cli.model_cli.show_error')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_download_exception(self, mock_logger, mock_show_error):
        """Test handling exception in download operation."""
        mock_backend = Mock()
        mock_backend.list_models.return_value = []
        mock_backend.download_model.side_effect = Exception("Download error")
        params = {'model': 'test-model', 'force': False}
        
        handle_download(mock_backend, params)
        
        mock_show_error.assert_called_once()


class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    @patch('ali.cli.model_cli.console')
    @patch('click.prompt')
    @patch('ali.cli.model_cli.show_error')
    def test_select_model_invalid_input_then_valid(self, mock_show_error, mock_prompt, mock_console):
        """Test model selection with invalid input followed by valid input."""
        mock_backend = Mock()
        mock_model = Mock()
        mock_model.name = "Test Model"
        mock_model.id = "test-model"
        mock_backend.search_models.return_value = [mock_model]
        
        # First invalid, then valid
        mock_prompt.side_effect = ["invalid", "1"]
        
        result = select_model_for_download(mock_backend)
        
        assert result == "test-model"
        assert mock_prompt.call_count == 2
        mock_show_error.assert_called_once()
    
    def test_argument_parsing_edge_cases(self):
        """Test edge cases in argument parsing."""
        original_argv = sys.argv.copy()
        try:
            # Test with empty arguments
            sys.argv = ['model_cli.py']
            
            with patch('ali.cli.model_cli.show_help') as mock_help:
                main()
                mock_help.assert_called_once()
        finally:
            sys.argv = original_argv


class TestPerformance:
    """Test performance characteristics."""
    
    @patch('ali.cli.model_cli.console')
    @patch('ali.cli.model_cli.get_logger')
    def test_handle_list_many_models(self, mock_logger, mock_console):
        """Test listing many models performance."""
        mock_backend = Mock()
        mock_manager = Mock()
        
        # Create many mock models
        models = []
        for i in range(100):
            model = Mock()
            model.name = f"Model {i}"
            model.id = f"model{i}"
            model.size = "1GB"
            model.family = "test"
            models.append(model)
        
        mock_backend.list_models.return_value = models
        params = {'provider': 'ollama', 'verbose': False}
        
        import time
        start_time = time.time()
        
        handle_list(mock_backend, mock_manager, params)
        
        end_time = time.time()
        
        # Should handle many models quickly
        assert end_time - start_time < 2.0