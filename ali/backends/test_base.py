"""Unit tests for backend base functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from abc import ABC

from .base import BaseBackend, BackendError, ModelInfo


class TestModelInfo:
    """Test ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test ModelInfo creation with required fields."""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            size="1B",
            family="test",
            format="gguf"
        )
        
        assert model.id == "test-model"
        assert model.name == "Test Model"
        assert model.size == "1B"
        assert model.family == "test"
        assert model.format == "gguf"
        assert model.description is None  # Optional field
    
    def test_model_info_with_optional_fields(self):
        """Test ModelInfo creation with optional fields."""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            size="1B",
            family="test",
            format="gguf",
            description="A test model",
            version="1.0",
            tags=["test", "small"]
        )
        
        assert model.description == "A test model"
        assert model.version == "1.0"
        assert model.tags == ["test", "small"]
    
    def test_model_info_display_name_property(self):
        """Test display_name property returns name."""
        model = ModelInfo(
            id="org/model-1b",
            name="Model 1B",
            size="1B",
            family="test",
            format="gguf"
        )
        
        assert model.display_name == "Model 1B"
    
    def test_model_info_equality(self):
        """Test ModelInfo equality comparison."""
        model1 = ModelInfo(
            id="test-model",
            name="Test Model",
            size="1B",
            family="test",
            format="gguf"
        )
        
        model2 = ModelInfo(
            id="test-model",
            name="Test Model", 
            size="1B",
            family="test",
            format="gguf"
        )
        
        model3 = ModelInfo(
            id="different-model",
            name="Different Model",
            size="1B",
            family="test",
            format="gguf"
        )
        
        assert model1 == model2
        assert model1 != model3
    
    def test_model_info_string_representation(self):
        """Test ModelInfo string representation."""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            size="1B",
            family="test",
            format="gguf"
        )
        
        str_repr = str(model)
        assert "Test Model" in str_repr
        assert "1B" in str_repr


class TestBackendError:
    """Test BackendError exception class."""
    
    def test_backend_error_creation(self):
        """Test BackendError creation."""
        error = BackendError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_backend_error_with_cause(self):
        """Test BackendError with underlying cause."""
        original_error = ValueError("Original error")
        backend_error = BackendError("Backend error") from original_error
        
        assert str(backend_error) == "Backend error"
        assert backend_error.__cause__ == original_error
    
    def test_backend_error_inheritance(self):
        """Test BackendError inheritance."""
        error = BackendError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, BackendError)


class ConcreteBackend(BaseBackend):
    """Concrete implementation for testing BaseBackend."""
    
    def __init__(self):
        super().__init__()
        self.mock_models = []
        self.mock_running = []
    
    def list_models(self):
        return self.mock_models
    
    def pull_model(self, model_id: str, progress_callback=None):
        model = ModelInfo(
            id=model_id,
            name=model_id,
            size="1B",
            family="test",
            format="gguf"
        )
        if model not in self.mock_models:
            self.mock_models.append(model)
        return model
    
    def remove_model(self, model_id: str):
        self.mock_models = [m for m in self.mock_models if m.id != model_id]
        return True
    
    def run_model(self, model_id: str, prompt: str, **kwargs):
        if not any(m.id == model_id for m in self.mock_models):
            raise BackendError(f"Model {model_id} not found")
        return f"Response to: {prompt}"
    
    def stop_model(self, model_id: str):
        self.mock_running = [m for m in self.mock_running if m != model_id]
        return True
    
    def list_running_models(self):
        return self.mock_running
    
    def get_model_info(self, model_id: str):
        for model in self.mock_models:
            if model.id == model_id:
                return model
        raise BackendError(f"Model {model_id} not found")


class TestBaseBackend:
    """Test BaseBackend abstract class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = ConcreteBackend()
    
    def test_backend_is_abstract(self):
        """Test that BaseBackend is abstract."""
        assert BaseBackend.__abstractmethods__
        
        # Should not be able to instantiate BaseBackend directly
        with pytest.raises(TypeError):
            BaseBackend()
    
    def test_concrete_backend_instantiation(self):
        """Test concrete backend instantiation."""
        backend = ConcreteBackend()
        assert isinstance(backend, BaseBackend)
        assert hasattr(backend, 'list_models')
        assert hasattr(backend, 'pull_model')
        assert hasattr(backend, 'remove_model')
        assert hasattr(backend, 'run_model')
    
    def test_list_models_empty(self):
        """Test list_models when no models are available."""
        models = self.backend.list_models()
        assert models == []
    
    def test_pull_model_success(self):
        """Test successful model pulling."""
        model = self.backend.pull_model("test-model")
        
        assert isinstance(model, ModelInfo)
        assert model.id == "test-model"
        assert model in self.backend.list_models()
    
    def test_pull_model_with_callback(self):
        """Test model pulling with progress callback."""
        callback_calls = []
        
        def progress_callback(message):
            callback_calls.append(message)
        
        model = self.backend.pull_model("test-model", progress_callback)
        
        assert isinstance(model, ModelInfo)
        # Callback may or may not be called depending on implementation
    
    def test_remove_model_success(self):
        """Test successful model removal."""
        # First add a model
        self.backend.pull_model("test-model")
        assert len(self.backend.list_models()) == 1
        
        # Then remove it
        result = self.backend.remove_model("test-model")
        assert result is True
        assert len(self.backend.list_models()) == 0
    
    def test_remove_nonexistent_model(self):
        """Test removing a model that doesn't exist."""
        result = self.backend.remove_model("nonexistent-model")
        # Should still return True (idempotent)
        assert result is True
    
    def test_run_model_success(self):
        """Test successful model execution."""
        # First add a model
        self.backend.pull_model("test-model")
        
        response = self.backend.run_model("test-model", "Hello")
        assert response == "Response to: Hello"
    
    def test_run_model_not_found(self):
        """Test running a model that doesn't exist."""
        with pytest.raises(BackendError):
            self.backend.run_model("nonexistent-model", "Hello")
    
    def test_run_model_with_kwargs(self):
        """Test running model with additional parameters."""
        self.backend.pull_model("test-model")
        
        response = self.backend.run_model(
            "test-model", 
            "Hello",
            temperature=0.7,
            max_tokens=100
        )
        assert response == "Response to: Hello"
    
    def test_stop_model(self):
        """Test stopping a model."""
        result = self.backend.stop_model("test-model")
        assert result is True
    
    def test_list_running_models_empty(self):
        """Test listing running models when none are running."""
        running = self.backend.list_running_models()
        assert running == []
    
    def test_get_model_info_success(self):
        """Test getting model info for existing model."""
        self.backend.pull_model("test-model")
        
        info = self.backend.get_model_info("test-model")
        assert isinstance(info, ModelInfo)
        assert info.id == "test-model"
    
    def test_get_model_info_not_found(self):
        """Test getting model info for nonexistent model."""
        with pytest.raises(BackendError):
            self.backend.get_model_info("nonexistent-model")


class TestBackendMethodSignatures:
    """Test that backend methods have correct signatures."""
    
    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        required_methods = [
            'list_models',
            'pull_model', 
            'remove_model',
            'run_model',
            'stop_model',
            'list_running_models',
            'get_model_info'
        ]
        
        for method_name in required_methods:
            assert hasattr(BaseBackend, method_name)
            assert method_name in BaseBackend.__abstractmethods__
    
    def test_method_signatures(self):
        """Test that abstract methods have correct signatures."""
        import inspect
        
        # Check pull_model signature
        sig = inspect.signature(BaseBackend.pull_model)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'model_id' in params
        assert 'progress_callback' in params
        
        # Check run_model signature
        sig = inspect.signature(BaseBackend.run_model)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'model_id' in params
        assert 'prompt' in params
        assert 'kwargs' in params


class TestBackendIntegration:
    """Integration tests for backend functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = ConcreteBackend()
    
    def test_full_model_lifecycle(self):
        """Test complete model lifecycle: pull -> info -> run -> remove."""
        model_id = "lifecycle-test-model"
        
        # Initially no models
        assert len(self.backend.list_models()) == 0
        
        # Pull model
        model = self.backend.pull_model(model_id)
        assert model.id == model_id
        assert len(self.backend.list_models()) == 1
        
        # Get model info
        info = self.backend.get_model_info(model_id)
        assert info.id == model_id
        
        # Run model
        response = self.backend.run_model(model_id, "Test prompt")
        assert "Test prompt" in response
        
        # Remove model
        result = self.backend.remove_model(model_id)
        assert result is True
        assert len(self.backend.list_models()) == 0
    
    def test_multiple_models(self):
        """Test handling multiple models."""
        model_ids = ["model1", "model2", "model3"]
        
        # Pull multiple models
        for model_id in model_ids:
            self.backend.pull_model(model_id)
        
        assert len(self.backend.list_models()) == 3
        
        # Verify all models are listed
        listed_models = self.backend.list_models()
        listed_ids = [m.id for m in listed_models]
        
        for model_id in model_ids:
            assert model_id in listed_ids
        
        # Run each model
        for model_id in model_ids:
            response = self.backend.run_model(model_id, f"Hello from {model_id}")
            assert model_id in response
        
        # Remove one model
        self.backend.remove_model("model2")
        assert len(self.backend.list_models()) == 2
        
        # Verify specific model was removed
        remaining_ids = [m.id for m in self.backend.list_models()]
        assert "model1" in remaining_ids
        assert "model2" not in remaining_ids
        assert "model3" in remaining_ids
    
    def test_error_handling_integration(self):
        """Test error handling across backend operations."""
        # Try to run non-existent model
        with pytest.raises(BackendError):
            self.backend.run_model("nonexistent", "Hello")
        
        # Try to get info for non-existent model
        with pytest.raises(BackendError):
            self.backend.get_model_info("nonexistent")
        
        # Removing non-existent model should not raise (idempotent)
        result = self.backend.remove_model("nonexistent")
        assert result is True


class TestBackendExtensions:
    """Test backend extension patterns."""
    
    def test_backend_subclassing(self):
        """Test that backends can be properly subclassed."""
        class ExtendedBackend(ConcreteBackend):
            def __init__(self):
                super().__init__()
                self.extended_feature = True
            
            def custom_method(self):
                return "extended functionality"
        
        backend = ExtendedBackend()
        assert isinstance(backend, BaseBackend)
        assert isinstance(backend, ConcreteBackend)
        assert backend.extended_feature is True
        assert backend.custom_method() == "extended functionality"
        
        # Should still have all base functionality
        model = backend.pull_model("test")
        assert isinstance(model, ModelInfo)
    
    def test_backend_method_override(self):
        """Test that backend methods can be overridden."""
        class CustomBackend(ConcreteBackend):
            def run_model(self, model_id: str, prompt: str, **kwargs):
                # Custom implementation
                return f"Custom response for {model_id}: {prompt}"
        
        backend = CustomBackend()
        backend.pull_model("test-model")
        
        response = backend.run_model("test-model", "Hello")
        assert response == "Custom response for test-model: Hello"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = ConcreteBackend()
    
    def test_empty_model_id(self):
        """Test handling of empty model ID."""
        # Different backends may handle this differently
        try:
            self.backend.pull_model("")
        except (BackendError, ValueError):
            pass  # Acceptable to raise error
    
    def test_none_model_id(self):
        """Test handling of None model ID."""
        with pytest.raises((BackendError, TypeError, AttributeError)):
            self.backend.pull_model(None)
    
    def test_unicode_model_id(self):
        """Test handling of unicode characters in model ID."""
        unicode_id = "模型-🤖-test"
        model = self.backend.pull_model(unicode_id)
        assert model.id == unicode_id
    
    def test_very_long_model_id(self):
        """Test handling of very long model ID."""
        long_id = "a" * 1000
        model = self.backend.pull_model(long_id)
        assert model.id == long_id
    
    def test_special_characters_in_prompt(self):
        """Test handling of special characters in prompts."""
        self.backend.pull_model("test-model")
        
        special_prompt = "Hello\n\t\"world\" & <test> 🌍"
        response = self.backend.run_model("test-model", special_prompt)
        assert special_prompt in response
    
    def test_model_info_with_none_values(self):
        """Test ModelInfo creation with None values for optional fields."""
        model = ModelInfo(
            id="test",
            name="Test",
            size=None,
            family=None,
            format="gguf",
            description=None
        )
        
        assert model.size is None
        assert model.family is None
        assert model.description is None