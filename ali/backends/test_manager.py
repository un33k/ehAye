"""Unit tests for backend manager functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from .manager import BackendManager, get_backend_manager, get_backend
from .base import BaseBackend, ModelInfo, ChatMessage, GenerationConfig


class MockBackend(BaseBackend):
    """Mock backend for testing."""
    
    def __init__(self, name: str, available: bool = True):
        self.name = name
        self._available = available
        self._models = []
    
    def is_available(self) -> bool:
        return self._available
    
    def list_models(self):
        return self._models
    
    def search_models(self, query=None):
        if query:
            return [m for m in self._models if query.lower() in m.name.lower()]
        return self._models
    
    def download_model(self, model_id, progress_callback=None):
        model = ModelInfo(id=model_id, name=f"Model {model_id}")
        self._models.append(model)
        return model
    
    def remove_model(self, model_id):
        self._models = [m for m in self._models if m.id != model_id]
        return True
    
    def get_model_info(self, model_id):
        for model in self._models:
            if model.id == model_id:
                return model
        return None
    
    def generate(self, model_id, messages, config):
        yield f"Response from {self.name}:{model_id}"
    
    def load_model(self, model_id):
        return True
    
    def unload_model(self, model_id):
        return True


class TestBackendManager:
    """Test BackendManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset global manager for each test
        import ali.backends.manager as manager_module
        manager_module._backend_manager = None
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_initialization(self, mock_mlx, mock_ollama):
        """Test BackendManager initialization."""
        # Mock backends
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        # Should initialize ollama but not mlx
        backends = manager.list_backends()
        assert "ollama" in backends
        assert "mlx" not in backends
        
        mock_ollama.assert_called_once()
        mock_mlx.assert_called_once()
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_initialization_no_backends_available(self, mock_mlx, mock_ollama):
        """Test initialization when no backends are available."""
        mock_ollama_instance = MockBackend("ollama", available=False)
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        backends = manager.list_backends()
        assert len(backends) == 0
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    @patch('ali.backends.manager.get_config')
    def test_get_backend_default(self, mock_config, mock_mlx, mock_ollama):
        """Test getting default backend."""
        # Setup mocks
        mock_config_obj = Mock()
        mock_config_obj.models.default_backend = "ollama"
        mock_config.return_value = mock_config_obj
        
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=True)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        backend = manager.get_backend()
        assert backend.name == "ollama"
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_get_backend_by_name(self, mock_mlx, mock_ollama):
        """Test getting backend by specific name."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=True)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        ollama_backend = manager.get_backend("ollama")
        mlx_backend = manager.get_backend("mlx")
        
        assert ollama_backend.name == "ollama"
        assert mlx_backend.name == "mlx"
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_get_backend_fallback(self, mock_mlx, mock_ollama):
        """Test backend fallback when requested backend unavailable."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        # Request unavailable backend, should fallback to available one
        backend = manager.get_backend("mlx")
        assert backend.name == "ollama"
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_get_backend_no_backends_available(self, mock_mlx, mock_ollama):
        """Test getting backend when none are available."""
        mock_ollama_instance = MockBackend("ollama", available=False)
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        with pytest.raises(RuntimeError, match="No backends available"):
            manager.get_backend("ollama")
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_is_backend_available(self, mock_mlx, mock_ollama):
        """Test checking backend availability."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        assert manager.is_backend_available("ollama") is True
        assert manager.is_backend_available("mlx") is False
        assert manager.is_backend_available("nonexistent") is False
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_list_all_models(self, mock_mlx, mock_ollama):
        """Test listing models from all backends."""
        # Setup backends with models
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance._models = [
            ModelInfo(id="ollama-model1", name="Ollama Model 1"),
            ModelInfo(id="ollama-model2", name="Ollama Model 2")
        ]
        
        mock_mlx_instance = MockBackend("mlx", available=True)
        mock_mlx_instance._models = [
            ModelInfo(id="mlx-model1", name="MLX Model 1")
        ]
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        all_models = manager.list_all_models()
        
        assert "ollama" in all_models
        assert "mlx" in all_models
        assert len(all_models["ollama"]) == 2
        assert len(all_models["mlx"]) == 1
        assert all_models["ollama"][0].id == "ollama-model1"
        assert all_models["mlx"][0].id == "mlx-model1"
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_list_models_specific_backend(self, mock_mlx, mock_ollama):
        """Test listing models from specific backend."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance._models = [
            ModelInfo(id="ollama-model", name="Ollama Model")
        ]
        
        mock_mlx_instance = MockBackend("mlx", available=True)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        ollama_models = manager.list_all_models(backend="ollama")
        
        assert "ollama" in ollama_models
        assert "mlx" not in ollama_models
        assert len(ollama_models["ollama"]) == 1
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_list_models_nonexistent_backend(self, mock_mlx, mock_ollama):
        """Test listing models from nonexistent backend."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        result = manager.list_all_models(backend="nonexistent")
        assert result == {}
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_list_models_backend_error(self, mock_mlx, mock_ollama):
        """Test handling error when listing models from backend."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance.list_models = Mock(side_effect=Exception("Backend error"))
        
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        all_models = manager.list_all_models()
        
        # Should return empty list for backend with error
        assert "ollama" in all_models
        assert all_models["ollama"] == []
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_search_all_models(self, mock_mlx, mock_ollama):
        """Test searching models across all backends."""
        # Setup backends with searchable models
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance._models = [
            ModelInfo(id="phi3", name="Phi-3 Model"),
            ModelInfo(id="llama", name="Llama Model")
        ]
        
        mock_mlx_instance = MockBackend("mlx", available=True)
        mock_mlx_instance._models = [
            ModelInfo(id="phi3-mlx", name="Phi-3 MLX Model")
        ]
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        # Search for "phi" models
        results = manager.search_all_models(query="phi")
        
        assert "ollama" in results
        assert "mlx" in results
        assert len(results["ollama"]) == 1  # phi3
        assert len(results["mlx"]) == 1     # phi3-mlx
        assert results["ollama"][0].id == "phi3"
        assert results["mlx"][0].id == "phi3-mlx"
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_search_models_specific_backend(self, mock_mlx, mock_ollama):
        """Test searching models in specific backend."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance._models = [
            ModelInfo(id="test-model", name="Test Model")
        ]
        
        mock_mlx_instance = MockBackend("mlx", available=True)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        results = manager.search_all_models(query="test", backend="ollama")
        
        assert "ollama" in results
        assert "mlx" not in results
        assert len(results["ollama"]) == 1


class TestGlobalFunctions:
    """Test global manager functions."""
    
    def setup_method(self):
        """Reset global manager for each test."""
        import ali.backends.manager as manager_module
        manager_module._backend_manager = None
    
    @patch('ali.backends.manager.BackendManager')
    def test_get_backend_manager_singleton(self, mock_manager_class):
        """Test get_backend_manager returns singleton."""
        mock_instance = Mock()
        mock_manager_class.return_value = mock_instance
        
        # First call creates instance
        manager1 = get_backend_manager()
        
        # Second call returns same instance
        manager2 = get_backend_manager()
        
        assert manager1 is manager2
        mock_manager_class.assert_called_once()
    
    @patch('ali.backends.manager.get_backend_manager')
    def test_get_backend_function(self, mock_get_manager):
        """Test get_backend convenience function."""
        mock_manager = Mock()
        mock_backend = Mock()
        mock_manager.get_backend.return_value = mock_backend
        mock_get_manager.return_value = mock_manager
        
        backend = get_backend("test-backend")
        
        assert backend is mock_backend
        mock_manager.get_backend.assert_called_once_with("test-backend")
    
    @patch('ali.backends.manager.get_backend_manager')
    def test_get_backend_function_default(self, mock_get_manager):
        """Test get_backend function with default backend."""
        mock_manager = Mock()
        mock_backend = Mock()
        mock_manager.get_backend.return_value = mock_backend
        mock_get_manager.return_value = mock_manager
        
        backend = get_backend()
        
        assert backend is mock_backend
        mock_manager.get_backend.assert_called_once_with(None)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Reset global manager for each test."""
        import ali.backends.manager as manager_module
        manager_module._backend_manager = None
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_backend_initialization_exceptions(self, mock_mlx, mock_ollama):
        """Test handling exceptions during backend initialization."""
        # Make Ollama initialization raise exception
        mock_ollama.side_effect = Exception("Ollama init error")
        mock_mlx_instance = MockBackend("mlx", available=True)
        mock_mlx.return_value = mock_mlx_instance
        
        # Should not crash, should continue with available backends
        manager = BackendManager()
        
        backends = manager.list_backends()
        assert "mlx" in backends
        assert "ollama" not in backends
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_search_models_with_none_query(self, mock_mlx, mock_ollama):
        """Test searching models with None query."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance._models = [ModelInfo(id="test", name="Test")]
        
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        results = manager.search_all_models(query=None)
        assert "ollama" in results
        assert len(results["ollama"]) == 1
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    def test_search_models_backend_error(self, mock_mlx, mock_ollama):
        """Test handling error when searching models."""
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_ollama_instance.search_models = Mock(side_effect=Exception("Search error"))
        
        mock_mlx_instance = MockBackend("mlx", available=False)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        manager = BackendManager()
        
        results = manager.search_all_models(query="test")
        
        # Should return empty list for backend with error
        assert "ollama" in results
        assert results["ollama"] == []


class TestIntegration:
    """Test integration scenarios."""
    
    def setup_method(self):
        """Reset global manager for each test."""
        import ali.backends.manager as manager_module
        manager_module._backend_manager = None
    
    @patch('ali.backends.manager.OllamaBackend')
    @patch('ali.backends.manager.MLXBackend')
    @patch('ali.backends.manager.get_config')
    def test_complete_workflow(self, mock_config, mock_mlx, mock_ollama):
        """Test complete backend manager workflow."""
        # Setup config
        mock_config_obj = Mock()
        mock_config_obj.models.default_backend = "ollama"
        mock_config.return_value = mock_config_obj
        
        # Setup backends
        mock_ollama_instance = MockBackend("ollama", available=True)
        mock_mlx_instance = MockBackend("mlx", available=True)
        
        mock_ollama.return_value = mock_ollama_instance
        mock_mlx.return_value = mock_mlx_instance
        
        # Test workflow
        manager = get_backend_manager()
        
        # Check available backends
        backends = manager.list_backends()
        assert len(backends) == 2
        assert "ollama" in backends
        assert "mlx" in backends
        
        # Get default backend
        default_backend = manager.get_backend()
        assert default_backend.name == "ollama"
        
        # Add some models and search
        mock_ollama_instance.download_model("test-model")
        
        all_models = manager.list_all_models()
        assert len(all_models["ollama"]) == 1
        
        search_results = manager.search_all_models("test")
        assert len(search_results["ollama"]) == 1