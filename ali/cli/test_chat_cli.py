"""Unit tests for chat CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess
from click.testing import CliRunner

from .chat_cli import (
    GenerationConfig,
    ChatSession,
    create_chat_session,
    get_chat_session,
    get_installed_models,
    search_models,
    select_model_interactive,
    start_chat_loop,
    show_chat_help,
    show_chat_settings,
    app
)


class TestGenerationConfig:
    """Test GenerationConfig class."""
    
    def test_default_initialization(self):
        """Test default GenerationConfig initialization."""
        config = GenerationConfig()
        assert config.max_tokens == 512
        assert config.temperature == 0.7
    
    def test_custom_initialization(self):
        """Test custom GenerationConfig initialization."""
        config = GenerationConfig(max_tokens=1024, temperature=0.5)
        assert config.max_tokens == 1024
        assert config.temperature == 0.5


class TestChatSession:
    """Test ChatSession class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GenerationConfig()
        self.session = ChatSession("test-model", self.config, "Test system prompt")
    
    def test_initialization(self):
        """Test ChatSession initialization."""
        assert self.session.model_id == "test-model"
        assert self.session.generation_config == self.config
        assert self.session.conversation.system_prompt == "Test system prompt"
        assert self.session.conversation.messages == []
    
    @patch('subprocess.run')
    def test_send_message_success(self, mock_run):
        """Test successful message sending."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Test response from model"
        mock_run.return_value = mock_result
        
        response = self.session.send_message("Hello", streaming=False)
        
        assert response == "Test response from model"
        mock_run.assert_called_once_with(
            ['ollama', 'run', 'test-model', 'Hello'],
            capture_output=True, text=True, timeout=60
        )
    
    @patch('subprocess.run')
    def test_send_message_error(self, mock_run):
        """Test message sending with error."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Model not found"
        mock_run.return_value = mock_result
        
        response = self.session.send_message("Hello")
        
        assert "Error: Model not found" in response
    
    @patch('subprocess.run')
    def test_send_message_model_not_found(self, mock_run):
        """Test message sending with model not found error."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "pull model first"
        mock_run.return_value = mock_result
        
        response = self.session.send_message("Hello")
        
        assert "Try: ollama pull test-model" in response
    
    @patch('subprocess.run')
    def test_send_message_timeout(self, mock_run):
        """Test message sending with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(['ollama'], 60)
        
        response = self.session.send_message("Hello")
        
        assert "timed out" in response.lower()
    
    @patch('subprocess.run')
    def test_send_message_exception(self, mock_run):
        """Test message sending with exception."""
        mock_run.side_effect = Exception("Connection error")
        
        response = self.session.send_message("Hello")
        
        assert "Error: Connection error" in response
    
    def test_clear_conversation(self):
        """Test conversation clearing."""
        self.session.conversation.messages = ["msg1", "msg2"]
        self.session.clear_conversation()
        assert self.session.conversation.messages == []
    
    def test_save_conversation(self):
        """Test conversation saving (placeholder)."""
        # Currently just a placeholder, should not raise
        self.session.save_conversation()


class TestModelFunctions:
    """Test model-related functions."""
    
    @patch('subprocess.run')
    def test_get_installed_models_success(self, mock_run):
        """Test successful model listing."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """NAME                     ID              SIZE      MODIFIED     
phi3:latest              4f2222927938    2.2 GB    26 hours ago    
qwen2:0.5b               6f48b936a09f    352 MB    38 hours ago    
gemma2:2b                8ccf136fdd52    1.6 GB    38 hours ago"""
        mock_run.return_value = mock_result
        
        models = get_installed_models()
        
        assert len(models) == 3
        assert models[0].id == "phi3:latest"
        assert models[0].display_name == "phi3:latest"
        assert models[0].category == "ollama"
        assert models[1].id == "qwen2:0.5b"
        assert models[2].id == "gemma2:2b"
    
    @patch('subprocess.run')
    def test_get_installed_models_failure(self, mock_run):
        """Test model listing failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        models = get_installed_models()
        assert models == []
    
    @patch('subprocess.run')
    def test_get_installed_models_exception(self, mock_run):
        """Test model listing with exception."""
        mock_run.side_effect = Exception("Connection error")
        
        models = get_installed_models()
        assert models == []
    
    @patch('ali.cli.chat_cli.get_installed_models')
    def test_search_models_no_query(self, mock_get_models):
        """Test search models without query."""
        mock_models = [Mock(display_name="test-model")]
        mock_get_models.return_value = mock_models
        
        result = search_models()
        assert result == mock_models
    
    @patch('ali.cli.chat_cli.get_installed_models')
    def test_search_models_with_query(self, mock_get_models):
        """Test search models with query."""
        model1 = Mock(display_name="phi3:latest")
        model2 = Mock(display_name="qwen2:0.5b")
        model3 = Mock(display_name="gemma2:2b")
        mock_get_models.return_value = [model1, model2, model3]
        
        result = search_models("phi")
        assert len(result) == 1
        assert result[0] == model1
        
        result = search_models("2")
        assert len(result) == 2
        assert model2 in result
        assert model3 in result


class TestSessionFunctions:
    """Test session management functions."""
    
    def test_create_chat_session(self):
        """Test chat session creation."""
        config = GenerationConfig()
        session = create_chat_session("test-model", config, "system prompt")
        
        assert isinstance(session, ChatSession)
        assert session.model_id == "test-model"
        assert session.generation_config == config
        assert session.conversation.system_prompt == "system prompt"
    
    def test_get_chat_session(self):
        """Test chat session retrieval."""
        session = ChatSession("test", GenerationConfig())
        result = get_chat_session(session)
        assert result == session


class TestInteractiveFunctions:
    """Test interactive functions."""
    
    @patch('ali.cli.chat_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_model_interactive_success(self, mock_prompt, mock_get_models):
        """Test successful interactive model selection."""
        model1 = Mock(id="model1", display_name="Model 1")
        model2 = Mock(id="model2", display_name="Model 2")
        mock_get_models.return_value = [model1, model2]
        mock_prompt.return_value = 1
        
        result = select_model_interactive()
        assert result == "model1"
    
    @patch('ali.cli.chat_cli.get_installed_models')
    def test_select_model_interactive_no_models(self, mock_get_models):
        """Test interactive model selection with no models."""
        mock_get_models.return_value = []
        
        result = select_model_interactive()
        assert result is None
    
    @patch('ali.cli.chat_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_model_interactive_invalid_choice(self, mock_prompt, mock_get_models):
        """Test interactive model selection with invalid choice."""
        model1 = Mock(id="model1", display_name="Model 1")
        mock_get_models.return_value = [model1]
        mock_prompt.return_value = 5  # Invalid choice
        
        result = select_model_interactive()
        assert result is None
    
    @patch('ali.cli.chat_cli.get_installed_models')
    @patch('click.prompt')
    def test_select_model_interactive_abort(self, mock_prompt, mock_get_models):
        """Test interactive model selection with user abort."""
        model1 = Mock(id="model1", display_name="Model 1")
        mock_get_models.return_value = [model1]
        mock_prompt.side_effect = click.Abort()
        
        result = select_model_interactive()
        assert result is None


class TestDisplayFunctions:
    """Test display functions."""
    
    @patch('ali.cli.chat_cli.console')
    def test_show_chat_help(self, mock_console):
        """Test chat help display."""
        show_chat_help()
        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "Available Commands" in args
        assert "quit" in args
        assert "clear" in args
    
    @patch('ali.cli.chat_cli.console')
    def test_show_chat_settings(self, mock_console):
        """Test chat settings display."""
        session = ChatSession("test-model", GenerationConfig(max_tokens=256, temperature=0.8))
        session.conversation.messages = ["msg1", "msg2"]
        
        show_chat_settings(session)
        
        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]
        assert "test-model" in args
        assert "0.8" in args
        assert "256" in args
        assert "2" in args  # Number of messages


class TestChatLoop:
    """Test chat loop functionality."""
    
    @patch('ali.cli.chat_cli.console')
    def test_start_chat_loop_no_session(self, mock_console):
        """Test chat loop with no session."""
        start_chat_loop(None)
        # Should call show_error and return early
        # Since show_error is imported, it would be called
    
    @patch('ali.cli.chat_cli.console')
    @patch('builtins.input', side_effect=['quit'])
    def test_start_chat_loop_quit_command(self, mock_input, mock_console):
        """Test chat loop with quit command."""
        session = ChatSession("test", GenerationConfig())
        
        # Mock console.input to return 'quit'
        mock_console.input.return_value = 'quit'
        
        start_chat_loop(session)
        
        # Should print startup messages and goodbye
        assert mock_console.print.call_count >= 3  # Startup + goodbye


class TestCLICommands:
    """Test CLI command integration."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    def test_app_help(self):
        """Test chat app help command."""
        result = self.runner.invoke(app, ['--help'])
        assert result.exit_code == 0
        assert "Interactive chat with LLM models" in result.output
        assert "interactive" in result.output
        assert "single" in result.output
        assert "models" in result.output
    
    @patch('ali.cli.chat_cli.get_installed_models')
    def test_models_command(self, mock_get_models):
        """Test models command."""
        model = Mock(display_name="Test Model", id="test", category="test")
        mock_get_models.return_value = [model]
        
        result = self.runner.invoke(app, ['models'])
        assert result.exit_code == 0
        assert "Available Models" in result.output
        assert "Test Model" in result.output
    
    @patch('ali.cli.chat_cli.get_installed_models')
    def test_models_command_no_models(self, mock_get_models):
        """Test models command with no models."""
        mock_get_models.return_value = []
        
        result = self.runner.invoke(app, ['models'])
        assert result.exit_code == 0
        assert "No models found" in result.output


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_generation_config_edge_values(self):
        """Test GenerationConfig with edge values."""
        config = GenerationConfig(max_tokens=0, temperature=0.0)
        assert config.max_tokens == 0
        assert config.temperature == 0.0
        
        config = GenerationConfig(max_tokens=10000, temperature=2.0)
        assert config.max_tokens == 10000
        assert config.temperature == 2.0
    
    @patch('subprocess.run')
    def test_get_installed_models_empty_output(self, mock_run):
        """Test model listing with empty output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "NAME                     ID              SIZE      MODIFIED\n"
        mock_run.return_value = mock_result
        
        models = get_installed_models()
        assert models == []
    
    @patch('subprocess.run')
    def test_get_installed_models_malformed_output(self, mock_run):
        """Test model listing with malformed output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "NAME\nmalformed line\n"
        mock_run.return_value = mock_result
        
        models = get_installed_models()
        assert models == []