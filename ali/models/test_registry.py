"""Unit tests for model registry functionality."""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import os

from .registry import ModelRegistry, get_installed_models, register_model, find_model, search_models
from .categories import ModelInfo


class TestModelRegistry:
    """Test ModelRegistry class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('ali.models.registry.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.models.categories = ['tiny', 'small', 'medium', 'large', 'code']
            mock_config_obj.paths.models_dir = Path('/test/models')
            mock_config.return_value = mock_config_obj
            
            self.registry = ModelRegistry()
    
    def test_initialization(self):
        """Test ModelRegistry initialization."""
        assert self.registry.config is not None
        assert self.registry._installed_cache is None
    
    def test_get_model_list_file(self):
        """Test getting model list file path."""
        result = self.registry.get_model_list_file('tiny')
        expected = Path('/test/models/tiny/.model_list')
        assert result == expected
    
    @patch('builtins.open', new_callable=mock_open, read_data="model_id:phi3:mini\nmodel_id:qwen2:0.5b\n")
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_read_installed_models_success(self, mock_stat, mock_exists, mock_file):
        """Test successful reading of installed models."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 100
        
        models = self.registry.read_installed_models('tiny')
        
        assert len(models) == 2
        assert 'phi3:mini' in models
        assert 'qwen2:0.5b' in models
    
    @patch('pathlib.Path.exists')
    def test_read_installed_models_file_not_exists(self, mock_exists):
        """Test reading models when file doesn't exist."""
        mock_exists.return_value = False
        
        models = self.registry.read_installed_models('tiny')
        
        assert models == []
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_read_installed_models_empty_file(self, mock_stat, mock_exists):
        """Test reading models from empty file."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 0
        
        models = self.registry.read_installed_models('tiny')
        
        assert models == []
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    def test_write_model_to_category_new_model(self, mock_read, mock_mkdir, mock_file):
        """Test writing new model to category."""
        mock_read.return_value = []  # No existing models
        
        self.registry.write_model_to_category('phi3:mini', 'tiny')
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with('model_id:phi3:mini\n')
    
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    def test_write_model_to_category_existing_model(self, mock_read):
        """Test writing model that already exists."""
        mock_read.return_value = ['phi3:mini']  # Model already exists
        
        # Should not raise exception, just log debug message
        self.registry.write_model_to_category('phi3:mini', 'tiny')
        
        mock_read.assert_called_once_with('tiny')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    def test_remove_model_from_category_success(self, mock_read, mock_exists, mock_file):
        """Test successful model removal from category."""
        mock_exists.return_value = True
        mock_read.return_value = ['phi3:mini', 'qwen2:0.5b']
        
        result = self.registry.remove_model_from_category('phi3:mini', 'tiny')
        
        assert result is True
        mock_file.assert_called_once()
        # Should write remaining model
        mock_file().write.assert_called_once_with('model_id:qwen2:0.5b\n')
    
    @patch('pathlib.Path.exists')
    def test_remove_model_from_category_file_not_exists(self, mock_exists):
        """Test removing model when category file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.registry.remove_model_from_category('phi3:mini', 'tiny')
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    def test_remove_model_from_category_model_not_found(self, mock_read, mock_exists):
        """Test removing model that doesn't exist in category."""
        mock_exists.return_value = True
        mock_read.return_value = ['qwen2:0.5b']  # Different model
        
        result = self.registry.remove_model_from_category('phi3:mini', 'tiny')
        
        assert result is False
    
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    @patch('ali.models.registry.categorize_model')
    def test_get_all_installed_success(self, mock_categorize, mock_read):
        """Test getting all installed models."""
        # Mock reading from different categories
        mock_read.side_effect = [
            ['phi3:mini'],     # tiny
            ['llama3:8b'],     # small
            [],                # medium
            [],                # large
            ['codellama:7b']   # code
        ]
        
        # Mock categorize_model responses
        def categorize_side_effect(model_id):
            if model_id == 'phi3:mini':
                return ModelInfo(
                    id='phi3:mini',
                    name='Phi-3 Mini',
                    category='tiny',
                    size_gb=2.3
                )
            elif model_id == 'llama3:8b':
                return ModelInfo(
                    id='llama3:8b',
                    name='Llama 3 8B',
                    category='medium',
                    size_gb=8.0
                )
            elif model_id == 'codellama:7b':
                return ModelInfo(
                    id='codellama:7b',
                    name='Code Llama 7B',
                    category='code',
                    size_gb=7.0
                )
        
        mock_categorize.side_effect = categorize_side_effect
        
        models = self.registry.get_all_installed()
        
        assert len(models) == 3
        assert models[0].id == 'phi3:mini'
        assert models[1].id == 'llama3:8b'
        assert models[2].id == 'codellama:7b'
        
        # Check category override
        assert models[1].category == 'small'  # Overridden from 'medium'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_get_all_installed_cached(self, mock_get_all):
        """Test cached model retrieval."""
        mock_models = [Mock()]
        self.registry._installed_cache = mock_models
        
        result = self.registry.get_all_installed()
        
        assert result == mock_models
        mock_get_all.assert_not_called()
    
    @patch('ali.models.registry.ModelRegistry.write_model_to_category')
    @patch('ali.models.registry.categorize_model')
    def test_register_model_success(self, mock_categorize, mock_write):
        """Test successful model registration."""
        mock_model_info = ModelInfo(
            id='phi3:mini',
            name='Phi-3 Mini',
            category='tiny',
            size_gb=2.3
        )
        mock_categorize.return_value = mock_model_info
        
        result = self.registry.register_model('phi3:mini')
        
        assert result.id == 'phi3:mini'
        assert result.category == 'tiny'
        mock_write.assert_called_once_with('phi3:mini', 'tiny')
        assert self.registry._installed_cache is None
    
    @patch('ali.models.registry.ModelRegistry.write_model_to_category')
    @patch('ali.models.registry.categorize_model')
    def test_register_model_with_custom_category(self, mock_categorize, mock_write):
        """Test registering model with custom category."""
        mock_model_info = ModelInfo(
            id='phi3:mini',
            name='Phi-3 Mini',
            category='tiny',
            size_gb=2.3
        )
        mock_categorize.return_value = mock_model_info
        
        result = self.registry.register_model('phi3:mini', category='small')
        
        assert result.category == 'small'
        mock_write.assert_called_once_with('phi3:mini', 'small')
    
    @patch('ali.models.registry.ModelRegistry.write_model_to_category')
    @patch('ali.models.registry.categorize_model')
    def test_register_model_invalid_category(self, mock_categorize, mock_write):
        """Test registering model with invalid category."""
        mock_model_info = ModelInfo(
            id='phi3:mini',
            name='Phi-3 Mini',
            category='invalid',
            size_gb=2.3
        )
        mock_categorize.return_value = mock_model_info
        
        result = self.registry.register_model('phi3:mini')
        
        assert result.category == 'medium'  # Fallback category
        mock_write.assert_called_once_with('phi3:mini', 'medium')
    
    @patch('ali.models.registry.ModelRegistry.remove_model_from_category')
    def test_unregister_model_success(self, mock_remove):
        """Test successful model unregistration."""
        mock_remove.side_effect = [False, True, False, False, False]  # Only found in 'small'
        
        result = self.registry.unregister_model('phi3:mini')
        
        assert result is True
        assert mock_remove.call_count == 5  # Called for each category
        assert self.registry._installed_cache is None
    
    @patch('ali.models.registry.ModelRegistry.remove_model_from_category')
    def test_unregister_model_not_found(self, mock_remove):
        """Test unregistering model that doesn't exist."""
        mock_remove.return_value = False
        
        result = self.registry.unregister_model('nonexistent')
        
        assert result is False
        assert mock_remove.call_count == 5
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_find_model_success(self, mock_get_all):
        """Test finding existing model."""
        mock_models = [
            ModelInfo(id='phi3:mini', name='Phi-3 Mini', category='tiny'),
            ModelInfo(id='llama3:8b', name='Llama 3 8B', category='medium')
        ]
        mock_get_all.return_value = mock_models
        
        result = self.registry.find_model('phi3:mini')
        
        assert result is not None
        assert result.id == 'phi3:mini'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_find_model_not_found(self, mock_get_all):
        """Test finding non-existent model."""
        mock_get_all.return_value = []
        
        result = self.registry.find_model('nonexistent')
        
        assert result is None
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_search_installed_no_filters(self, mock_get_all):
        """Test searching without filters."""
        mock_models = [
            ModelInfo(id='phi3:mini', name='Phi-3 Mini', category='tiny'),
            ModelInfo(id='llama3:8b', name='Llama 3 8B', category='medium')
        ]
        mock_get_all.return_value = mock_models
        
        result = self.registry.search_installed()
        
        assert len(result) == 2
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_search_installed_with_query(self, mock_get_all):
        """Test searching with query filter."""
        mock_models = [
            ModelInfo(id='phi3:mini', name='Phi-3 Mini', category='tiny'),
            ModelInfo(id='llama3:8b', name='Llama 3 8B', category='medium')
        ]
        mock_get_all.return_value = mock_models
        
        result = self.registry.search_installed(query='phi')
        
        assert len(result) == 1
        assert result[0].id == 'phi3:mini'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_search_installed_with_category(self, mock_get_all):
        """Test searching with category filter."""
        mock_models = [
            ModelInfo(id='phi3:mini', name='Phi-3 Mini', category='tiny'),
            ModelInfo(id='llama3:8b', name='Llama 3 8B', category='medium')
        ]
        mock_get_all.return_value = mock_models
        
        result = self.registry.search_installed(category='tiny')
        
        assert len(result) == 1
        assert result[0].id == 'phi3:mini'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_search_installed_with_size_filter(self, mock_get_all):
        """Test searching with size filter."""
        mock_models = [
            ModelInfo(id='phi3:mini', name='Phi-3 Mini', category='tiny', size_params='3.8B'),
            ModelInfo(id='llama3:8b', name='Llama 3 8B', category='medium', size_params='8B')
        ]
        mock_get_all.return_value = mock_models
        
        result = self.registry.search_installed(size_filter='3.8B')
        
        assert len(result) == 1
        assert result[0].id == 'phi3:mini'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_get_category_stats(self, mock_get_all):
        """Test getting category statistics."""
        mock_models = [
            ModelInfo(id='phi3:mini', name='Phi-3 Mini', category='tiny'),
            ModelInfo(id='qwen2:0.5b', name='Qwen2 0.5B', category='tiny'),
            ModelInfo(id='llama3:8b', name='Llama 3 8B', category='medium')
        ]
        mock_get_all.return_value = mock_models
        
        stats = self.registry.get_category_stats()
        
        assert stats['tiny'] == 2
        assert stats['small'] == 0
        assert stats['medium'] == 1
        assert stats['large'] == 0
        assert stats['code'] == 0
    
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.unlink')
    def test_cleanup_empty_categories(self, mock_unlink, mock_exists, mock_read):
        """Test cleaning up empty category files."""
        mock_exists.return_value = True
        mock_read.side_effect = [[], ['model1'], [], [], []]  # Empty, not empty, empty, empty, empty
        
        self.registry.cleanup_empty_categories()
        
        # Should remove 4 empty files (tiny, medium, large, code)
        assert mock_unlink.call_count == 4


class TestGlobalFunctions:
    """Test global registry functions."""
    
    @patch('ali.models.registry.model_registry')
    def test_get_installed_models(self, mock_registry):
        """Test getting installed models via global function."""
        mock_models = [ModelInfo(id='test', name='Test', category='tiny')]
        mock_registry.get_all_installed.return_value = mock_models
        
        result = get_installed_models()
        
        assert result == mock_models
        mock_registry.get_all_installed.assert_called_once()
    
    @patch('ali.models.registry.model_registry')
    def test_register_model_function(self, mock_registry):
        """Test registering model via global function."""
        mock_model = ModelInfo(id='test', name='Test', category='tiny')
        mock_registry.register_model.return_value = mock_model
        
        result = register_model('test', 'tiny')
        
        assert result == mock_model
        mock_registry.register_model.assert_called_once_with('test', 'tiny')
    
    @patch('ali.models.registry.model_registry')
    def test_find_model_function(self, mock_registry):
        """Test finding model via global function."""
        mock_model = ModelInfo(id='test', name='Test', category='tiny')
        mock_registry.find_model.return_value = mock_model
        
        result = find_model('test')
        
        assert result == mock_model
        mock_registry.find_model.assert_called_once_with('test')
    
    @patch('ali.models.registry.model_registry')
    def test_search_models_function(self, mock_registry):
        """Test searching models via global function."""
        mock_models = [ModelInfo(id='test', name='Test', category='tiny')]
        mock_registry.search_installed.return_value = mock_models
        
        result = search_models(query='test', category='tiny', size_filter='3B')
        
        assert result == mock_models
        mock_registry.search_installed.assert_called_once_with('test', 'tiny', '3B')


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('ali.models.registry.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.models.categories = ['tiny', 'small', 'medium', 'large', 'code']
            mock_config_obj.paths.models_dir = Path('/test/models')
            mock_config.return_value = mock_config_obj
            
            self.registry = ModelRegistry()
    
    @patch('builtins.open', side_effect=IOError("Read error"))
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_read_installed_models_error(self, mock_stat, mock_exists, mock_file):
        """Test handling read error."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 100
        
        models = self.registry.read_installed_models('tiny')
        
        assert models == []
    
    @patch('builtins.open', side_effect=IOError("Write error"))
    @patch('pathlib.Path.mkdir')
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    def test_write_model_to_category_error(self, mock_read, mock_mkdir, mock_file):
        """Test handling write error."""
        mock_read.return_value = []
        
        with pytest.raises(Exception):  # Should raise ModelError
            self.registry.write_model_to_category('phi3:mini', 'tiny')
    
    @patch('builtins.open', side_effect=IOError("Write error"))
    @patch('pathlib.Path.exists')
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    def test_remove_model_from_category_error(self, mock_read, mock_exists, mock_file):
        """Test handling remove error."""
        mock_exists.return_value = True
        mock_read.return_value = ['phi3:mini']
        
        result = self.registry.remove_model_from_category('phi3:mini', 'tiny')
        
        assert result is False
    
    @patch('pathlib.Path.unlink', side_effect=OSError("Delete error"))
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    @patch('pathlib.Path.exists')
    def test_cleanup_empty_categories_error(self, mock_exists, mock_read, mock_unlink):
        """Test handling cleanup error."""
        mock_exists.return_value = True
        mock_read.return_value = []
        
        # Should not raise exception
        self.registry.cleanup_empty_categories()


class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('ali.models.registry.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.models.categories = ['tiny', 'small', 'medium', 'large', 'code']
            mock_config_obj.paths.models_dir = Path('/test/models')
            mock_config.return_value = mock_config_obj
            
            self.registry = ModelRegistry()
    
    @patch('builtins.open', new_callable=mock_open, read_data="invalid line\nmodel_id:\nmodel_id:valid_model\n")
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_read_installed_models_malformed_data(self, mock_stat, mock_exists, mock_file):
        """Test reading models with malformed data."""
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 100
        
        models = self.registry.read_installed_models('tiny')
        
        # Should only get valid model
        assert len(models) == 1
        assert models[0] == 'valid_model'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_search_installed_case_insensitive(self, mock_get_all):
        """Test case-insensitive search."""
        mock_models = [
            ModelInfo(id='PHI3:mini', name='Phi-3 Mini', category='tiny'),
            ModelInfo(id='llama3:8b', name='LLAMA 3 8B', category='medium')
        ]
        mock_get_all.return_value = mock_models
        
        result = self.registry.search_installed(query='phi')
        
        assert len(result) == 1
        assert result[0].id == 'PHI3:mini'
    
    @patch('ali.models.registry.ModelRegistry.get_all_installed')
    def test_get_category_stats_unknown_category(self, mock_get_all):
        """Test category stats with unknown category."""
        mock_models = [
            ModelInfo(id='test', name='Test', category='unknown_category')
        ]
        mock_get_all.return_value = mock_models
        
        stats = self.registry.get_category_stats()
        
        assert stats.get('unknown', 0) == 1


class TestPerformance:
    """Test performance characteristics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('ali.models.registry.get_config') as mock_config:
            mock_config_obj = Mock()
            mock_config_obj.models.categories = ['tiny', 'small', 'medium', 'large', 'code']
            mock_config_obj.paths.models_dir = Path('/test/models')
            mock_config.return_value = mock_config_obj
            
            self.registry = ModelRegistry()
    
    @patch('ali.models.registry.ModelRegistry.read_installed_models')
    @patch('ali.models.registry.categorize_model')
    def test_get_all_installed_performance(self, mock_categorize, mock_read):
        """Test performance with many models."""
        # Mock many models in each category
        mock_read.side_effect = [
            [f'model{i}' for i in range(20)],  # tiny: 20 models
            [f'model{i+20}' for i in range(20)],  # small: 20 models
            [],  # medium: empty
            [],  # large: empty
            []   # code: empty
        ]
        
        def categorize_side_effect(model_id):
            return ModelInfo(
                id=model_id,
                name=f'Model {model_id}',
                category='tiny',
                size_gb=1.0
            )
        
        mock_categorize.side_effect = categorize_side_effect
        
        import time
        start_time = time.time()
        
        models = self.registry.get_all_installed()
        
        end_time = time.time()
        
        assert len(models) == 40
        # Should handle many models quickly
        assert end_time - start_time < 1.0