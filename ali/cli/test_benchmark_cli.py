"""Unit tests for benchmark CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import click

from .benchmark_cli import app, select_model_interactive, select_models_interactive, main


class TestBenchmarkCLI:
    """Test benchmark CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test benchmark CLI help command."""
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert "Performance benchmarking" in result.output
        assert "single" in result.output
        assert "compare" in result.output
        assert "validate" in result.output
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.benchmark_model')
    @patch('ali.cli.benchmark_cli.print_benchmark_report')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark(self, mock_setup, mock_print, mock_benchmark, mock_validate):
        """Test single model benchmark."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_result = Mock()
        mock_benchmark.return_value = mock_result
        
        result = self.runner.invoke(app, ['single', '--model', 'test-model', '--tokens', '50', '--runs', '2'])
        
        assert result.exit_code == 0
        mock_validate.assert_called_once()
        mock_benchmark.assert_called_once_with('test-model', 50, 2)
        mock_print.assert_called_once_with(mock_result)
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.select_model_interactive')
    @patch('ali.cli.benchmark_cli.benchmark_model')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark_interactive_model_selection(self, mock_setup, mock_benchmark, mock_select, mock_validate):
        """Test single benchmark with interactive model selection."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_select.return_value = "selected-model"
        mock_benchmark.return_value = Mock()
        
        result = self.runner.invoke(app, ['single'])
        
        assert result.exit_code == 0
        mock_select.assert_called_once()
        mock_benchmark.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark_validation_failed(self, mock_setup, mock_validate):
        """Test single benchmark when validation fails."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = False
        
        result = self.runner.invoke(app, ['single', '--model', 'test-model'])
        
        assert result.exit_code == 0  # Command succeeds but doesn't run benchmark
        mock_validate.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.select_model_interactive')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark_no_model_selected(self, mock_setup, mock_select, mock_validate):
        """Test single benchmark when no model is selected."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_select.return_value = None  # No model selected
        
        result = self.runner.invoke(app, ['single'])
        
        assert result.exit_code == 0
        mock_select.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.benchmark_model')
    @patch('ali.cli.benchmark_cli.export_results_to_json')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark_with_output(self, mock_setup, mock_export, mock_benchmark, mock_validate):
        """Test single benchmark with JSON output."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_result = Mock()
        mock_benchmark.return_value = mock_result
        mock_export.return_value = True
        
        result = self.runner.invoke(app, ['single', '--model', 'test-model', '--output', 'results.json'])
        
        assert result.exit_code == 0
        mock_export.assert_called_once_with([mock_result], 'results.json')
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.compare_models')
    @patch('ali.cli.benchmark_cli.print_comparison_report')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_compare_models(self, mock_setup, mock_print, mock_compare, mock_validate):
        """Test model comparison."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_results = [Mock(), Mock()]
        mock_compare.return_value = mock_results
        
        result = self.runner.invoke(app, ['compare', '--models', 'model1', '--models', 'model2'])
        
        assert result.exit_code == 0
        mock_validate.assert_called_once()
        mock_compare.assert_called_once_with(['model1', 'model2'], 100, 2)
        mock_print.assert_called_once_with(mock_results)
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('ali.cli.benchmark_cli.compare_models')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_compare_all_models(self, mock_setup, mock_compare, mock_get_models, mock_validate):
        """Test comparing all installed models."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        
        # Mock installed models
        mock_model1 = Mock()
        mock_model1.id = "model1"
        mock_model2 = Mock()
        mock_model2.id = "model2"
        mock_get_models.return_value = [mock_model1, mock_model2]
        
        mock_compare.return_value = [Mock(), Mock()]
        
        result = self.runner.invoke(app, ['compare', '--all'])
        
        assert result.exit_code == 0
        mock_get_models.assert_called_once()
        mock_compare.assert_called_once_with(['model1', 'model2'], 100, 2)
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.select_models_interactive')
    @patch('ali.cli.benchmark_cli.compare_models')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_compare_interactive_selection(self, mock_setup, mock_compare, mock_select, mock_validate):
        """Test comparison with interactive model selection."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_select.return_value = ['model1', 'model2']
        mock_compare.return_value = [Mock(), Mock()]
        
        result = self.runner.invoke(app, ['compare'])
        
        assert result.exit_code == 0
        mock_select.assert_called_once()
        mock_compare.assert_called_once_with(['model1', 'model2'], 100, 2)
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_compare_insufficient_models(self, mock_setup, mock_validate):
        """Test comparison with insufficient models."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        
        result = self.runner.invoke(app, ['compare', '--models', 'single-model'])
        
        assert result.exit_code == 0  # Command succeeds but shows error message
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.compare_models')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_compare_no_successful_benchmarks(self, mock_setup, mock_compare, mock_validate):
        """Test comparison when no benchmarks succeed."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_compare.return_value = []  # No successful results
        
        result = self.runner.invoke(app, ['compare', '--models', 'model1', '--models', 'model2'])
        
        assert result.exit_code == 0
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_list_models(self, mock_setup, mock_get_models):
        """Test listing models for benchmarking."""
        mock_setup.return_value = Mock()
        
        # Mock models
        mock_model = Mock()
        mock_model.display_name = "Test Model"
        mock_model.id = "test-model"
        mock_model.category = "medium"
        mock_model.size_gb = 3.8
        mock_get_models.return_value = [mock_model]
        
        result = self.runner.invoke(app, ['list-models'])
        
        assert result.exit_code == 0
        assert "Test Model" in result.output
        mock_get_models.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.search_models')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_list_models_with_search(self, mock_setup, mock_search):
        """Test listing models with search query."""
        mock_setup.return_value = Mock()
        
        mock_model = Mock()
        mock_model.display_name = "Phi Model"
        mock_model.id = "phi3"
        mock_model.category = "small"
        mock_search.return_value = [mock_model]
        
        result = self.runner.invoke(app, ['list-models', '--search', 'phi'])
        
        assert result.exit_code == 0
        assert "Phi Model" in result.output
        mock_search.assert_called_once_with(query='phi')
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_list_models_empty(self, mock_setup, mock_get_models):
        """Test listing models when none are found."""
        mock_setup.return_value = Mock()
        mock_get_models.return_value = []
        
        result = self.runner.invoke(app, ['list-models'])
        
        assert result.exit_code == 0
        assert "No models found" in result.output
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_validate_success(self, mock_setup, mock_validate):
        """Test environment validation success."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        
        result = self.runner.invoke(app, ['validate'])
        
        assert result.exit_code == 0
        assert "validation passed" in result.output
        mock_validate.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_validate_failure(self, mock_setup, mock_validate):
        """Test environment validation failure."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = False
        
        result = self.runner.invoke(app, ['validate'])
        
        assert result.exit_code == 0
        assert "validation failed" in result.output


class TestInteractiveFunctions:
    """Test interactive selection functions."""
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_model_interactive_success(self, mock_prompt, mock_get_models):
        """Test successful interactive model selection."""
        # Mock models
        mock_model = Mock()
        mock_model.display_name = "Test Model"
        mock_model.id = "test-model"
        mock_get_models.return_value = [mock_model]
        
        # Mock user choice
        mock_prompt.return_value = 1
        
        result = select_model_interactive()
        
        assert result == "test-model"
        mock_prompt.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    def test_select_model_interactive_no_models(self, mock_get_models):
        """Test interactive selection when no models available."""
        mock_get_models.return_value = []
        
        result = select_model_interactive()
        
        assert result is None
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_model_interactive_invalid_choice(self, mock_prompt, mock_get_models):
        """Test interactive selection with invalid choice."""
        mock_model = Mock()
        mock_model.display_name = "Test Model"
        mock_get_models.return_value = [mock_model]
        
        # Mock invalid choice
        mock_prompt.return_value = 99
        
        result = select_model_interactive()
        
        assert result is None
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_model_interactive_abort(self, mock_prompt, mock_get_models):
        """Test interactive selection when user aborts."""
        mock_model = Mock()
        mock_get_models.return_value = [mock_model]
        
        # Mock abort
        mock_prompt.side_effect = click.Abort()
        
        result = select_model_interactive()
        
        assert result is None
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_models_interactive_single_selection(self, mock_prompt, mock_get_models):
        """Test interactive multiple model selection with single choice."""
        # Mock models
        mock_model1 = Mock()
        mock_model1.display_name = "Model 1"
        mock_model1.id = "model1"
        mock_model2 = Mock()
        mock_model2.display_name = "Model 2"
        mock_model2.id = "model2"
        mock_get_models.return_value = [mock_model1, mock_model2]
        
        # Mock user choice
        mock_prompt.return_value = "1"
        
        result = select_models_interactive()
        
        assert result == ["model1"]
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_models_interactive_multiple_selection(self, mock_prompt, mock_get_models):
        """Test interactive multiple model selection with comma-separated choices."""
        # Mock models
        models = []
        for i in range(3):
            model = Mock()
            model.display_name = f"Model {i+1}"
            model.id = f"model{i+1}"
            models.append(model)
        mock_get_models.return_value = models
        
        # Mock user choice
        mock_prompt.return_value = "1,3"
        
        result = select_models_interactive()
        
        assert result == ["model1", "model3"]
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_models_interactive_range_selection(self, mock_prompt, mock_get_models):
        """Test interactive selection with range."""
        # Mock models
        models = []
        for i in range(4):
            model = Mock()
            model.display_name = f"Model {i+1}"
            model.id = f"model{i+1}"
            models.append(model)
        mock_get_models.return_value = models
        
        # Mock user choice
        mock_prompt.return_value = "2-4"
        
        result = select_models_interactive()
        
        assert result == ["model2", "model3", "model4"]
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_models_interactive_all_selection(self, mock_prompt, mock_get_models):
        """Test interactive selection of all models."""
        # Mock models
        models = []
        for i in range(3):
            model = Mock()
            model.display_name = f"Model {i+1}"
            model.id = f"model{i+1}"
            models.append(model)
        mock_get_models.return_value = models
        
        # Mock user choice
        mock_prompt.return_value = "all"
        
        result = select_models_interactive()
        
        assert result == ["model1", "model2", "model3"]
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    def test_select_models_interactive_no_models(self, mock_get_models):
        """Test interactive multiple selection when no models available."""
        mock_get_models.return_value = []
        
        result = select_models_interactive()
        
        assert result == []
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_models_interactive_invalid_selection(self, mock_prompt, mock_get_models):
        """Test interactive selection with invalid choices."""
        mock_model = Mock()
        mock_model.display_name = "Model 1"
        mock_model.id = "model1"
        mock_get_models.return_value = [mock_model]
        
        # Mock invalid choice
        mock_prompt.return_value = "99"
        
        result = select_models_interactive()
        
        assert result == []


class TestMainFunction:
    """Test main entry point function."""
    
    @patch('ali.cli.benchmark_cli.app')
    def test_main_normal(self, mock_app):
        """Test normal main function execution."""
        main()
        mock_app.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.app')
    @patch('ali.cli.benchmark_cli.handle_keyboard_interrupt')
    def test_main_keyboard_interrupt(self, mock_handle, mock_app):
        """Test main function with keyboard interrupt."""
        mock_app.side_effect = KeyboardInterrupt()
        
        main()
        
        mock_handle.assert_called_once()
    
    @patch('ali.cli.benchmark_cli.app')
    def test_main_exception(self, mock_app):
        """Test main function with general exception."""
        mock_app.side_effect = Exception("Test error")
        
        with pytest.raises(SystemExit):
            main()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.benchmark_cli.common_setup')
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    def test_single_benchmark_keyboard_interrupt(self, mock_validate, mock_setup):
        """Test single benchmark with keyboard interrupt."""
        mock_setup.return_value = Mock()
        mock_validate.side_effect = KeyboardInterrupt()
        
        result = self.runner.invoke(app, ['single', '--model', 'test-model'])
        
        # Should handle gracefully
        assert result.exit_code == 0
    
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark_exception(self, mock_setup):
        """Test single benchmark with general exception."""
        mock_base_cli = Mock()
        mock_setup.return_value = mock_base_cli
        
        # Make validate_benchmark_environment raise exception
        with patch('ali.cli.benchmark_cli.validate_benchmark_environment') as mock_validate:
            mock_validate.side_effect = Exception("Test error")
            
            result = self.runner.invoke(app, ['single', '--model', 'test-model'])
            
            # Should call error handler
            mock_base_cli.handle_error.assert_called_once()


class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_models_complex_input(self, mock_prompt, mock_get_models):
        """Test complex input parsing for model selection."""
        # Mock models
        models = []
        for i in range(10):
            model = Mock()
            model.display_name = f"Model {i+1}"
            model.id = f"model{i+1}"
            models.append(model)
        mock_get_models.return_value = models
        
        # Mock complex input: single, range, and individual
        mock_prompt.return_value = "1, 3-5, 8"
        
        result = select_models_interactive()
        
        expected = ["model1", "model3", "model4", "model5", "model8"]
        assert result == expected
    
    @patch('ali.cli.benchmark_cli.validate_benchmark_environment')
    @patch('ali.cli.benchmark_cli.benchmark_model')
    @patch('ali.cli.benchmark_cli.export_results_to_json')
    @patch('ali.cli.benchmark_cli.common_setup')
    def test_single_benchmark_save_failure(self, mock_setup, mock_export, mock_benchmark, mock_validate):
        """Test single benchmark when saving results fails."""
        mock_setup.return_value = Mock()
        mock_validate.return_value = True
        mock_benchmark.return_value = Mock()
        mock_export.return_value = False  # Save fails
        
        result = self.runner.invoke(app, ['single', '--model', 'test-model', '--output', 'results.json'])
        
        assert result.exit_code == 0
        # Should show error message about save failure


class TestPerformance:
    """Test performance characteristics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('ali.cli.benchmark_cli.get_installed_models')
    def test_list_models_performance(self, mock_get_models):
        """Test listing many models performance."""
        # Create many mock models
        models = []
        for i in range(100):
            model = Mock()
            model.display_name = f"Model {i}"
            model.id = f"model{i}"
            model.category = "test"
            model.size_gb = 1.0
            models.append(model)
        
        mock_get_models.return_value = models
        
        import time
        start_time = time.time()
        
        with patch('ali.cli.benchmark_cli.common_setup'):
            result = self.runner.invoke(app, ['list-models'])
        
        end_time = time.time()
        
        assert result.exit_code == 0
        # Should handle many models quickly
        assert end_time - start_time < 2.0