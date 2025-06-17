"""Integration tests for model management workflow."""

import pytest
from unittest.mock import patch, MagicMock

from ali.models.categories import ModelInfo
from ali.models.registry import ModelRegistry
from ali.models.manager import ModelManager


class TestModelWorkflow:
    """Test complete model management workflow."""
    
    def test_model_categorization_and_registry(self, test_config, sample_model_id):
        """Test model categorization and registry integration."""
        # Create registry with test config
        registry = ModelRegistry()
        registry.config = test_config
        
        # Test registering a model
        model_info = registry.register_model(sample_model_id, "medium")
        
        assert isinstance(model_info, ModelInfo)
        assert model_info.id == sample_model_id
        assert model_info.category == "medium"
        
        # Test finding the model
        found_model = registry.find_model(sample_model_id)
        assert found_model is not None
        assert found_model.id == sample_model_id
        
        # Test listing installed models
        installed = registry.get_all_installed()
        assert len(installed) == 1
        assert installed[0].id == sample_model_id
    
    def test_model_search_and_filtering(self, test_config, sample_models):
        """Test model search and filtering functionality."""
        registry = ModelRegistry()
        registry.config = test_config
        
        # Register multiple models
        for model_id in sample_models:
            registry.register_model(model_id)
        
        # Test category filtering
        medium_models = registry.search_installed(category="medium")
        assert len(medium_models) > 0
        assert all(m.category == "medium" for m in medium_models)
        
        # Test query search
        code_models = registry.search_installed(query="code")
        assert len(code_models) > 0
        assert all("code" in m.id.lower() for m in code_models)
        
        # Test size filtering
        small_models = registry.search_installed(size_filter="2b")
        assert len(small_models) > 0
    
    @patch('subprocess.run')
    def test_model_download_workflow(self, mock_subprocess, test_config):
        """Test model download workflow."""
        # Mock successful subprocess call
        mock_subprocess.return_value = MagicMock(returncode=0, stderr="")
        
        manager = ModelManager()
        manager.config = test_config
        
        # Test model download
        model_id = "test-org/test-model-7b"
        model_info = manager.download_model(model_id)
        
        assert isinstance(model_info, ModelInfo)
        assert model_info.id == model_id
        
        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "huggingface-cli" in call_args
        assert "download" in call_args
        assert model_id in call_args
    
    def test_model_removal_workflow(self, test_config, sample_model_id):
        """Test model removal workflow."""
        registry = ModelRegistry()
        registry.config = test_config
        
        # Register a model first
        registry.register_model(sample_model_id, "medium")
        
        # Verify it's installed
        assert registry.find_model(sample_model_id) is not None
        
        # Remove the model
        manager = ModelManager()
        manager.registry = registry
        
        success = manager.remove_model(sample_model_id)
        assert success
        
        # Verify it's gone
        assert registry.find_model(sample_model_id) is None
    
    def test_model_info_consistency(self, test_config):
        """Test consistency between categorization and registry."""
        from ali.models.categories import categorize_model
        
        registry = ModelRegistry()
        registry.config = test_config
        
        # Test model with known characteristics
        model_id = "test-org/mistral-7b-instruct-4bit"
        
        # Categorize directly
        direct_info = categorize_model(model_id)
        
        # Register and retrieve
        registry_info = registry.register_model(model_id)
        
        # Should have consistent basic info
        assert direct_info.id == registry_info.id
        assert direct_info.name == registry_info.name
        assert direct_info.size_params == registry_info.size_params
        assert direct_info.quantization == registry_info.quantization
    
    def test_category_statistics(self, test_config, sample_models):
        """Test category statistics generation."""
        registry = ModelRegistry()
        registry.config = test_config
        
        # Register models
        for model_id in sample_models:
            registry.register_model(model_id)
        
        # Get statistics
        stats = registry.get_category_stats()
        
        assert isinstance(stats, dict)
        assert all(isinstance(count, int) for count in stats.values())
        assert sum(stats.values()) == len(sample_models)