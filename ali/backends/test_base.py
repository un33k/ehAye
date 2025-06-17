"""Unit tests for backend base classes and data structures."""

import pytest
from dataclasses import FrozenInstanceError

from .base import ModelInfo, ChatMessage, GenerationConfig, BaseBackend


class TestModelInfo:
    """Test ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test ModelInfo creation with required fields."""
        model = ModelInfo(id="test-id", name="Test Model")
        assert model.id == "test-id"
        assert model.name == "Test Model"
        assert model.size is None
        assert model.description is None
        assert model.parameters is None
        assert model.family is None
        assert model.format is None
        assert model.installed is False
    
    def test_model_info_with_all_fields(self):
        """Test ModelInfo with all fields populated."""
        model = ModelInfo(
            id="phi3:mini",
            name="Phi-3 Mini",
            size="3.8GB",
            description="Small language model by Microsoft",
            parameters="3.8B",
            family="phi",
            format="gguf",
            installed=True
        )
        assert model.id == "phi3:mini"
        assert model.name == "Phi-3 Mini"
        assert model.size == "3.8GB"
        assert model.description == "Small language model by Microsoft"
        assert model.parameters == "3.8B"
        assert model.family == "phi"
        assert model.format == "gguf"
        assert model.installed is True
    
    def test_model_info_equality(self):
        """Test ModelInfo equality comparison."""
        model1 = ModelInfo(id="test", name="Test")
        model2 = ModelInfo(id="test", name="Test")
        model3 = ModelInfo(id="different", name="Test")
        
        assert model1 == model2
        assert model1 != model3
    
    def test_model_info_repr(self):
        """Test ModelInfo string representation."""
        model = ModelInfo(id="test", name="Test Model")
        repr_str = repr(model)
        assert "ModelInfo" in repr_str
        assert "test" in repr_str
        assert "Test Model" in repr_str


class TestChatMessage:
    """Test ChatMessage dataclass."""
    
    def test_chat_message_creation(self):
        """Test ChatMessage creation."""
        message = ChatMessage(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"
    
    def test_chat_message_roles(self):
        """Test different chat message roles."""
        user_msg = ChatMessage(role="user", content="Question")
        assistant_msg = ChatMessage(role="assistant", content="Answer")
        system_msg = ChatMessage(role="system", content="Instructions")
        
        assert user_msg.role == "user"
        assert assistant_msg.role == "assistant"
        assert system_msg.role == "system"
    
    def test_chat_message_equality(self):
        """Test ChatMessage equality."""
        msg1 = ChatMessage(role="user", content="Hello")
        msg2 = ChatMessage(role="user", content="Hello")
        msg3 = ChatMessage(role="user", content="Different")
        
        assert msg1 == msg2
        assert msg1 != msg3
    
    def test_chat_message_empty_content(self):
        """Test ChatMessage with empty content."""
        message = ChatMessage(role="user", content="")
        assert message.content == ""
    
    def test_chat_message_multiline_content(self):
        """Test ChatMessage with multiline content."""
        content = "This is a\nmultiline\nmessage"
        message = ChatMessage(role="user", content=content)
        assert message.content == content
        assert "\n" in message.content


class TestGenerationConfig:
    """Test GenerationConfig dataclass."""
    
    def test_generation_config_defaults(self):
        """Test GenerationConfig default values."""
        config = GenerationConfig()
        assert config.temperature == 0.7
        assert config.max_tokens == 512
        assert config.top_p == 0.9
        assert config.stop_sequences is None
        assert config.stream is False
    
    def test_generation_config_custom_values(self):
        """Test GenerationConfig with custom values."""
        config = GenerationConfig(
            temperature=1.0,
            max_tokens=1024,
            top_p=0.8,
            stop_sequences=["END", "STOP"],
            stream=True
        )
        assert config.temperature == 1.0
        assert config.max_tokens == 1024
        assert config.top_p == 0.8
        assert config.stop_sequences == ["END", "STOP"]
        assert config.stream is True
    
    def test_generation_config_temperature_bounds(self):
        """Test GenerationConfig with temperature edge values."""
        config_low = GenerationConfig(temperature=0.0)
        config_high = GenerationConfig(temperature=2.0)
        
        assert config_low.temperature == 0.0
        assert config_high.temperature == 2.0
    
    def test_generation_config_stop_sequences_types(self):
        """Test GenerationConfig with different stop sequence types."""
        config_empty = GenerationConfig(stop_sequences=[])
        config_single = GenerationConfig(stop_sequences=["END"])
        config_multiple = GenerationConfig(stop_sequences=["END", "STOP", "\n"])
        
        assert config_empty.stop_sequences == []
        assert config_single.stop_sequences == ["END"]
        assert len(config_multiple.stop_sequences) == 3


class MockBackend(BaseBackend):
    """Mock backend implementation for testing."""
    
    def __init__(self, available: bool = True):
        self._available = available
        self._models = []
        self._loaded_models = set()
    
    def is_available(self) -> bool:
        return self._available
    
    def list_models(self):
        return self._models
    
    def search_models(self, query=None):
        return []
    
    def download_model(self, model_id, progress_callback=None):
        model = ModelInfo(id=model_id, name=f"Model {model_id}", installed=True)
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
        yield f"Response from {model_id}"
    
    def load_model(self, model_id):
        self._loaded_models.add(model_id)
        return True
    
    def unload_model(self, model_id):
        self._loaded_models.discard(model_id)
        return True


class TestBaseBackend:
    """Test BaseBackend abstract class through mock implementation."""
    
    def test_backend_instantiation(self):
        """Test backend can be instantiated through concrete implementation."""
        backend = MockBackend()
        assert isinstance(backend, BaseBackend)
    
    def test_backend_availability(self):
        """Test backend availability checking."""
        available_backend = MockBackend(available=True)
        unavailable_backend = MockBackend(available=False)
        
        assert available_backend.is_available() is True
        assert unavailable_backend.is_available() is False
    
    def test_backend_model_lifecycle(self):
        """Test complete model lifecycle."""
        backend = MockBackend()
        
        # Initially no models
        assert len(backend.list_models()) == 0
        
        # Download model
        model = backend.download_model("test-model")
        assert model.id == "test-model"
        assert model.installed is True
        
        # Model appears in list
        models = backend.list_models()
        assert len(models) == 1
        assert models[0].id == "test-model"
        
        # Get model info
        info = backend.get_model_info("test-model")
        assert info is not None
        assert info.id == "test-model"
        
        # Load model
        assert backend.load_model("test-model") is True
        
        # Generate with model
        responses = list(backend.generate(
            "test-model",
            [ChatMessage("user", "Hello")],
            GenerationConfig()
        ))
        assert len(responses) > 0
        assert "test-model" in responses[0]
        
        # Unload model
        assert backend.unload_model("test-model") is True
        
        # Remove model
        assert backend.remove_model("test-model") is True
        assert len(backend.list_models()) == 0
    
    def test_backend_model_not_found(self):
        """Test backend behavior with non-existent model."""
        backend = MockBackend()
        
        info = backend.get_model_info("non-existent")
        assert info is None
    
    def test_backend_generation_with_config(self):
        """Test backend generation with different configs."""
        backend = MockBackend()
        backend.download_model("test-model")
        
        config = GenerationConfig(
            temperature=1.0,
            max_tokens=100,
            stream=True
        )
        
        responses = list(backend.generate(
            "test-model",
            [ChatMessage("user", "Test")],
            config
        ))
        
        assert len(responses) > 0


class TestBackendIntegration:
    """Test backend integration scenarios."""
    
    def test_multiple_backends(self):
        """Test multiple backend instances."""
        backend1 = MockBackend()
        backend2 = MockBackend()
        
        backend1.download_model("model1")
        backend2.download_model("model2")
        
        assert len(backend1.list_models()) == 1
        assert len(backend2.list_models()) == 1
        assert backend1.list_models()[0].id == "model1"
        assert backend2.list_models()[0].id == "model2"
    
    def test_backend_error_handling(self):
        """Test backend error scenarios."""
        backend = MockBackend(available=False)
        
        # Backend should still work even if marked unavailable
        model = backend.download_model("test")
        assert model.id == "test"
    
    def test_complex_chat_conversation(self):
        """Test complex multi-turn conversation."""
        backend = MockBackend()
        backend.download_model("chat-model")
        
        messages = [
            ChatMessage("system", "You are a helpful assistant"),
            ChatMessage("user", "What is 2+2?"),
            ChatMessage("assistant", "4"),
            ChatMessage("user", "What about 3+3?")
        ]
        
        config = GenerationConfig(temperature=0.1, max_tokens=50)
        
        responses = list(backend.generate("chat-model", messages, config))
        assert len(responses) > 0


class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def test_empty_model_id(self):
        """Test backend with empty model ID."""
        backend = MockBackend()
        
        model = backend.download_model("")
        assert model.id == ""
    
    def test_special_characters_in_model_id(self):
        """Test model IDs with special characters."""
        backend = MockBackend()
        
        special_id = "model-with-special@chars:latest"
        model = backend.download_model(special_id)
        assert model.id == special_id
    
    def test_unicode_in_chat_message(self):
        """Test chat messages with unicode content."""
        message = ChatMessage("user", "Hello 🌍 世界")
        assert "🌍" in message.content
        assert "世界" in message.content
    
    def test_very_long_chat_message(self):
        """Test very long chat message content."""
        long_content = "A" * 10000
        message = ChatMessage("user", long_content)
        assert len(message.content) == 10000
    
    def test_generation_config_extreme_values(self):
        """Test GenerationConfig with extreme values."""
        config = GenerationConfig(
            temperature=100.0,
            max_tokens=1000000,
            top_p=0.0001,
            stop_sequences=["A"] * 1000
        )
        
        assert config.temperature == 100.0
        assert config.max_tokens == 1000000
        assert len(config.stop_sequences) == 1000


class TestPerformance:
    """Test performance characteristics."""
    
    def test_model_info_creation_performance(self):
        """Test ModelInfo creation performance."""
        import time
        
        start_time = time.time()
        
        for i in range(1000):
            ModelInfo(id=f"model-{i}", name=f"Model {i}")
        
        end_time = time.time()
        
        # Should create 1000 models quickly
        assert end_time - start_time < 1.0
    
    def test_backend_operations_performance(self):
        """Test backend operations performance."""
        import time
        
        backend = MockBackend()
        
        start_time = time.time()
        
        # Perform multiple operations
        for i in range(100):
            backend.download_model(f"model-{i}")
            backend.list_models()
            backend.get_model_info(f"model-{i}")
        
        end_time = time.time()
        
        # Should handle 100 model operations quickly
        assert end_time - start_time < 2.0