"""Unit tests for Ollama backend implementation."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from typing import List

from .ollama_backend import OllamaBackend
from .base import ModelInfo, ChatMessage, GenerationConfig


class TestOllamaBackend:
    """Test OllamaBackend class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = OllamaBackend()
    
    def test_initialization(self):
        """Test OllamaBackend initialization."""
        assert self.backend.service_url == "http://localhost:11434"
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_is_available_success(self, mock_run):
        """Test is_available when Ollama is available."""
        mock_run.return_value.returncode = 0
        
        result = self.backend.is_available()
        assert result is True
        
        mock_run.assert_called_once_with(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_is_available_not_found(self, mock_run):
        """Test is_available when Ollama is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = self.backend.is_available()
        assert result is False
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_is_available_timeout(self, mock_run):
        """Test is_available when command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(["ollama"], 5)
        
        result = self.backend.is_available()
        assert result is False
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_is_available_error(self, mock_run):
        """Test is_available when command returns error."""
        mock_run.return_value.returncode = 1
        
        result = self.backend.is_available()
        assert result is False
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_list_models_success(self, mock_run):
        """Test listing models successfully."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = """NAME                ID         SIZE     MODIFIED
phi3:latest         abc123     2.3 GB   2 hours ago
llama3.2:1b         def456     1.3 GB   1 day ago"""
        
        models = self.backend.list_models()
        
        assert len(models) == 2
        assert models[0].id == "phi3:latest"
        assert models[0].name == "phi3:latest"
        assert models[0].size == "2.3 GB"
        assert models[0].installed is True
        
        assert models[1].id == "llama3.2:1b"
        assert models[1].size == "1.3 GB"
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_list_models_empty(self, mock_run):
        """Test listing models when none are installed."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "NAME                ID         SIZE     MODIFIED\n"
        
        models = self.backend.list_models()
        assert len(models) == 0
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_list_models_error(self, mock_run):
        """Test listing models when command fails."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Error"
        
        models = self.backend.list_models()
        assert len(models) == 0
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_list_models_malformed_output(self, mock_run):
        """Test listing models with malformed output."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "some random output\nwith no proper format"
        
        models = self.backend.list_models()
        # Should handle gracefully and return empty list
        assert len(models) == 0
    
    def test_search_models_all(self):
        """Test searching all available models."""
        models = self.backend.search_models()
        
        assert len(models) > 0
        # Check some expected models
        model_ids = [m.id for m in models]
        assert "llama3.2" in model_ids
        assert "phi3" in model_ids
        assert "gemma2" in model_ids
    
    def test_search_models_with_query(self):
        """Test searching models with specific query."""
        models = self.backend.search_models("llama")
        
        # Should return only models containing "llama"
        for model in models:
            assert "llama" in model.id.lower() or "llama" in model.name.lower()
    
    def test_search_models_case_insensitive(self):
        """Test search is case insensitive."""
        models_lower = self.backend.search_models("phi")
        models_upper = self.backend.search_models("PHI")
        
        assert len(models_lower) == len(models_upper)
        assert [m.id for m in models_lower] == [m.id for m in models_upper]
    
    def test_search_models_no_matches(self):
        """Test searching with query that has no matches."""
        models = self.backend.search_models("nonexistent")
        assert len(models) == 0
    
    @patch('ali.backends.ollama_backend.subprocess.Popen')
    def test_download_model_success(self, mock_popen):
        """Test successful model download."""
        # Mock the process
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [
            "pulling manifest\n",
            "downloading layer 1/3\n",
            "downloading layer 2/3\n", 
            "downloading layer 3/3\n",
            "verifying sha256 digest\n",
            "writing manifest\n",
            "removing any unused layers\n",
            "success\n",
            ""  # EOF
        ]
        mock_process.poll.side_effect = [None, None, None, None, None, None, None, None, 0]
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Mock progress callback
        progress_callback = Mock()
        
        result = self.backend.download_model("phi3:mini", progress_callback)
        
        assert result.id == "phi3:mini"
        assert result.name == "phi3:mini"
        assert result.installed is True
        
        # Verify progress callback was called
        assert progress_callback.call_count > 0
    
    @patch('ali.backends.ollama_backend.subprocess.Popen')
    def test_download_model_failure(self, mock_popen):
        """Test model download failure."""
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [
            "error: model not found\n",
            ""  # EOF
        ]
        mock_process.poll.side_effect = [None, 1]
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        
        with pytest.raises(RuntimeError, match="Download failed"):
            self.backend.download_model("nonexistent")
    
    @patch('ali.backends.ollama_backend.subprocess.Popen')
    @patch('ali.backends.ollama_backend.psutil')
    def test_download_model_keyboard_interrupt(self, mock_psutil, mock_popen):
        """Test model download with keyboard interrupt."""
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = KeyboardInterrupt()
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = 130
        mock_popen.return_value = mock_process
        
        # Mock psutil process iteration
        mock_psutil.process_iter.return_value = []
        
        with pytest.raises(RuntimeError, match="Download cancelled"):
            self.backend.download_model("phi3:mini")
        
        mock_process.terminate.assert_called_once()
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_remove_model_success(self, mock_run):
        """Test successful model removal."""
        mock_run.return_value.returncode = 0
        
        result = self.backend.remove_model("phi3:mini")
        assert result is True
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ollama" in args
        assert "rm" in args
        assert "phi3:mini" in args
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_remove_model_failure(self, mock_run):
        """Test model removal failure."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Model not found"
        
        result = self.backend.remove_model("nonexistent")
        assert result is False
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_remove_model_exception(self, mock_run):
        """Test model removal with exception."""
        mock_run.side_effect = Exception("Command failed")
        
        result = self.backend.remove_model("phi3:mini")
        assert result is False
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_get_model_info_success(self, mock_run):
        """Test getting model info successfully."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Phi-3 Mini model\nParameters: 3.8B\nSize: 2.3GB"
        
        info = self.backend.get_model_info("phi3:mini")
        
        assert info is not None
        assert info.id == "phi3:mini"
        assert info.name == "phi3:mini"
        assert info.description == "Phi-3 Mini model"
        assert info.installed is True
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_get_model_info_not_found(self, mock_run):
        """Test getting info for non-existent model."""
        mock_run.return_value.returncode = 1
        
        info = self.backend.get_model_info("nonexistent")
        assert info is None
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_get_model_info_exception(self, mock_run):
        """Test getting model info with exception."""
        mock_run.side_effect = Exception("Command failed")
        
        info = self.backend.get_model_info("phi3:mini")
        assert info is None
    
    def test_format_messages_single(self):
        """Test formatting single message."""
        messages = [ChatMessage("user", "Hello, world!")]
        
        result = self.backend._format_messages(messages)
        assert result == "Hello, world!"
    
    def test_format_messages_conversation(self):
        """Test formatting multi-turn conversation."""
        messages = [
            ChatMessage("system", "You are helpful"),
            ChatMessage("user", "What is 2+2?"),
            ChatMessage("assistant", "4"),
            ChatMessage("user", "What about 3+3?")
        ]
        
        result = self.backend._format_messages(messages)
        
        expected = "System: You are helpful\nUser: What is 2+2?\nAssistant: 4\nUser: What about 3+3?\nAssistant:"
        assert result == expected
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_generate_non_streaming(self, mock_run):
        """Test non-streaming text generation."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "This is a response from the model."
        
        messages = [ChatMessage("user", "Hello")]
        config = GenerationConfig(stream=False)
        
        responses = list(self.backend.generate("phi3:mini", messages, config))
        
        assert len(responses) == 1
        assert responses[0] == "This is a response from the model."
    
    @patch('ali.backends.ollama_backend.subprocess.Popen')
    def test_generate_streaming(self, mock_popen):
        """Test streaming text generation."""
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = [
            "This ",
            "is ",
            "a ",
            "streaming ",
            "response.\n",
            ""  # EOF
        ]
        mock_process.poll.side_effect = [None, None, None, None, None, 0]
        mock_popen.return_value = mock_process
        
        messages = [ChatMessage("user", "Hello")]
        config = GenerationConfig(stream=True)
        
        responses = list(self.backend.generate("phi3:mini", messages, config))
        
        assert len(responses) == 5
        assert responses[0] == "This "
        assert responses[4] == "streaming response."
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_generate_with_temperature(self, mock_run):
        """Test generation with custom temperature."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Response"
        
        messages = [ChatMessage("user", "Hello")]
        config = GenerationConfig(temperature=1.0, stream=False)
        
        list(self.backend.generate("phi3:mini", messages, config))
        
        # Check that temperature was passed in command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "--temperature" in args
        assert "1.0" in args
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_generate_error(self, mock_run):
        """Test generation with error."""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Model not found"
        
        messages = [ChatMessage("user", "Hello")]
        config = GenerationConfig(stream=False)
        
        responses = list(self.backend.generate("nonexistent", messages, config))
        
        assert len(responses) == 1
        assert "Error:" in responses[0]
        assert "Model not found" in responses[0]
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_load_model_success(self, mock_run):
        """Test successful model loading."""
        mock_run.return_value.returncode = 0
        
        result = self.backend.load_model("phi3:mini")
        assert result is True
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ollama" in args
        assert "generate" in args
        assert "phi3:mini" in args
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_load_model_failure(self, mock_run):
        """Test model loading failure."""
        mock_run.return_value.returncode = 1
        
        result = self.backend.load_model("nonexistent")
        assert result is False
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_load_model_exception(self, mock_run):
        """Test model loading with exception."""
        mock_run.side_effect = Exception("Command failed")
        
        result = self.backend.load_model("phi3:mini")
        assert result is False
    
    def test_unload_model(self):
        """Test model unloading (always succeeds for Ollama)."""
        result = self.backend.unload_model("phi3:mini")
        assert result is True
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_run_ollama_cmd_success(self, mock_run):
        """Test successful Ollama command execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        
        result = self.backend._run_ollama_cmd(["list"])
        
        assert result.returncode == 0
        assert result.stdout == "Success"
        mock_run.assert_called_once_with(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_run_ollama_cmd_timeout(self, mock_run):
        """Test Ollama command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(["ollama"], 30)
        
        with pytest.raises(subprocess.TimeoutExpired):
            self.backend._run_ollama_cmd(["list"])
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_run_ollama_cmd_not_found(self, mock_run):
        """Test Ollama command not found."""
        mock_run.side_effect = FileNotFoundError("ollama not found")
        
        with pytest.raises(FileNotFoundError):
            self.backend._run_ollama_cmd(["list"])
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_run_ollama_cmd_custom_timeout(self, mock_run):
        """Test Ollama command with custom timeout."""
        mock_run.return_value.returncode = 0
        
        self.backend._run_ollama_cmd(["list"], timeout=60)
        
        mock_run.assert_called_once_with(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=60
        )


class TestEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = OllamaBackend()
    
    def test_format_messages_empty(self):
        """Test formatting empty message list."""
        with pytest.raises(IndexError):
            self.backend._format_messages([])
    
    def test_format_messages_unknown_role(self):
        """Test formatting message with unknown role."""
        messages = [ChatMessage("unknown", "Hello")]
        
        result = self.backend._format_messages(messages)
        assert result == "Hello"
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    def test_list_models_with_unicode(self, mock_run):
        """Test listing models with unicode characters."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = """NAME                ID         SIZE     MODIFIED
模型:latest         abc123     2.3 GB   2 hours ago"""
        
        models = self.backend.list_models()
        
        assert len(models) == 1
        assert models[0].id == "模型:latest"
    
    def test_search_models_unicode_query(self):
        """Test searching with unicode query."""
        models = self.backend.search_models("🤖")
        # Should return empty list gracefully
        assert len(models) == 0
    
    @patch('ali.backends.ollama_backend.subprocess.Popen')
    def test_download_model_empty_model_id(self, mock_popen):
        """Test downloading model with empty ID."""
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = ["", ""]
        mock_process.poll.side_effect = [None, 1]
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        
        with pytest.raises(RuntimeError):
            self.backend.download_model("")
    
    def test_generation_config_extreme_values(self):
        """Test generation with extreme configuration values."""
        messages = [ChatMessage("user", "Hello")]
        config = GenerationConfig(
            temperature=100.0,
            max_tokens=1000000,
            top_p=0.0001,
            stream=False
        )
        
        # Should not crash, even if values are extreme
        with patch('ali.backends.ollama_backend.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Response"
            
            responses = list(self.backend.generate("phi3:mini", messages, config))
            assert len(responses) == 1


class TestIntegration:
    """Test integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = OllamaBackend()
    
    @patch('ali.backends.ollama_backend.subprocess.run')
    @patch('ali.backends.ollama_backend.subprocess.Popen')
    def test_complete_model_lifecycle(self, mock_popen, mock_run):
        """Test complete model lifecycle."""
        # Mock availability check
        mock_run.return_value.returncode = 0
        
        # Mock download
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = ["success\n", ""]
        mock_process.poll.side_effect = [None, 0]
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        # Download model
        model = self.backend.download_model("test-model")
        assert model.id == "test-model"
        
        # Mock list models to include our model
        mock_run.return_value.stdout = "test-model:latest abc123 1.0 GB 1 hour ago"
        models = self.backend.list_models()
        assert len(models) == 1
        
        # Mock model info
        mock_run.return_value.stdout = "Test model description"
        info = self.backend.get_model_info("test-model")
        assert info is not None
        
        # Mock generation
        mock_run.return_value.stdout = "Generated response"
        messages = [ChatMessage("user", "Hello")]
        responses = list(self.backend.generate("test-model", messages, GenerationConfig()))
        assert len(responses) == 1
        
        # Remove model
        result = self.backend.remove_model("test-model")
        assert result is True


class TestPerformance:
    """Test performance characteristics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.backend = OllamaBackend()
    
    def test_search_models_performance(self):
        """Test search models performance."""
        import time
        
        start_time = time.time()
        
        # Perform multiple searches
        for _ in range(100):
            self.backend.search_models("llama")
        
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0
    
    def test_format_messages_performance(self):
        """Test message formatting performance."""
        import time
        
        # Create large conversation
        messages = []
        for i in range(1000):
            messages.append(ChatMessage("user" if i % 2 == 0 else "assistant", f"Message {i}"))
        
        start_time = time.time()
        
        result = self.backend._format_messages(messages)
        
        end_time = time.time()
        
        # Should handle large conversations quickly
        assert end_time - start_time < 1.0
        assert len(result) > 0