"""Tests for LLM prompt formatting module."""

import pytest

from ehaye.llm.prompts import PromptFormatter, format_prompt, format_conversation


class TestPromptFormatter:
    """Test the prompt formatter."""
    
    def test_detect_model_type(self):
        """Test model type detection."""
        formatter = PromptFormatter()
        
        assert formatter.detect_model_type("mistral-7b-instruct") == "mistral"
        assert formatter.detect_model_type("llama-2-chat") == "llama"
        assert formatter.detect_model_type("phi-2-mlx") == "phi"
        assert formatter.detect_model_type("deepseek-coder") == "deepseek"
        assert formatter.detect_model_type("qwen-7b") == "qwen"
        assert formatter.detect_model_type("gemma-2b") == "gemma"
        assert formatter.detect_model_type("codellama-7b") == "codellama"
        assert formatter.detect_model_type("unknown-model") == "default"
    
    def test_format_prompt_mistral(self):
        """Test Mistral prompt formatting."""
        formatter = PromptFormatter()
        
        # Simple prompt
        result = formatter.format_prompt("Hello", "mistral-7b-instruct")
        assert result == "<s>[INST] Hello [/INST]"
        
        # With system prompt
        result = formatter.format_prompt(
            "Hello", 
            "mistral-7b-instruct", 
            system_prompt="You are helpful"
        )
        expected = "<s>[INST] <<SYS>>\nYou are helpful\n<</SYS>>\n\nHello [/INST]"
        assert result == expected
    
    def test_format_prompt_llama(self):
        """Test Llama prompt formatting."""
        formatter = PromptFormatter()
        
        result = formatter.format_prompt("Hello", "llama-2-chat")
        assert result == "### Human: Hello\n### Assistant:"
        
        # With system prompt
        result = formatter.format_prompt(
            "Hello", 
            "llama-2-chat", 
            system_prompt="You are helpful"
        )
        expected = "System: You are helpful\n\nUser: Hello\nAssistant:"
        assert result == expected
    
    def test_format_prompt_default(self):
        """Test default prompt formatting."""
        formatter = PromptFormatter()
        
        result = formatter.format_prompt("Hello", "unknown-model")
        assert result == "Hello"
        
        # With system prompt
        result = formatter.format_prompt(
            "Hello", 
            "unknown-model", 
            system_prompt="You are helpful"
        )
        expected = "System: You are helpful\n\nUser: Hello\nAssistant:"
        assert result == expected
    
    def test_format_conversation_mistral(self):
        """Test Mistral conversation formatting."""
        formatter = PromptFormatter()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = formatter.format_conversation(messages, "mistral-7b-instruct")
        
        # Should contain Mistral-specific formatting
        assert "[INST]" in result
        assert "[/INST]" in result
        assert result.startswith("<s>")
    
    def test_format_conversation_with_system(self):
        """Test conversation formatting with system prompt."""
        formatter = PromptFormatter()
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        result = formatter.format_conversation(
            messages, 
            "mistral-7b-instruct", 
            system_prompt="You are helpful"
        )
        
        assert "<<SYS>>" in result
        assert "You are helpful" in result


class TestModuleFunctions:
    """Test module-level functions."""
    
    def test_format_prompt_function(self):
        """Test the format_prompt function."""
        result = format_prompt("Test message", "phi-2-mlx")
        assert result == "Human: Test message\nAssistant:"
    
    def test_format_conversation_function(self):
        """Test the format_conversation function."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
        
        result = format_conversation(messages, "llama-2-chat")
        
        assert "### Human:" in result
        assert "### Assistant:" in result
        assert "Hello" in result
        assert "Hi!" in result