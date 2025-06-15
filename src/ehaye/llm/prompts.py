"""Prompt formatting for different model types."""

from typing import Dict, List, Optional

from ..core.logging import get_logger

logger = get_logger("llm.prompts")


class PromptFormatter:
    """Formats prompts for different model architectures."""
    
    TEMPLATES = {
        "mistral": "<s>[INST] {message} [/INST]",
        "llama": "### Human: {message}\n### Assistant:",
        "phi": "Human: {message}\nAssistant:",
        "deepseek": "User: {message}\n\nAssistant:",
        "qwen": "<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n",
        "gemma": "<start_of_turn>user\n{message}<end_of_turn>\n<start_of_turn>model\n",
        "codellama": "# Instruction\n{message}\n\n# Response\n",
        "instruct": "[INST] {message} [/INST]",
        "chat": "User: {message}\nAssistant:",
        "default": "{message}"
    }
    
    SYSTEM_TEMPLATES = {
        "mistral": "<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{message} [/INST]",
        "llama": "### System: {system}\n### Human: {message}\n### Assistant:",
        "qwen": "<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n",
        "gemma": "<start_of_turn>system\n{system}<end_of_turn>\n<start_of_turn>user\n{message}<end_of_turn>\n<start_of_turn>model\n",
        "default": "System: {system}\n\nUser: {message}\nAssistant:"
    }
    
    def detect_model_type(self, model_id: str) -> str:
        """Detect model type from model ID."""
        model_lower = model_id.lower()
        
        # Check for specific model families
        if "mistral" in model_lower:
            return "mistral"
        elif "llama" in model_lower:
            return "llama"
        elif "phi" in model_lower:
            return "phi"
        elif "deepseek" in model_lower:
            return "deepseek"
        elif "qwen" in model_lower:
            return "qwen"
        elif "gemma" in model_lower:
            return "gemma"
        elif "codellama" in model_lower or "code" in model_lower:
            return "codellama"
        elif "instruct" in model_lower:
            return "instruct"
        elif "chat" in model_lower:
            return "chat"
        else:
            return "default"
    
    def format_prompt(
        self, 
        message: str, 
        model_id: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Format a prompt for the given model."""
        model_type = self.detect_model_type(model_id)
        
        if system_prompt:
            template = self.SYSTEM_TEMPLATES.get(model_type, self.SYSTEM_TEMPLATES["default"])
            return template.format(system=system_prompt, message=message)
        else:
            template = self.TEMPLATES.get(model_type, self.TEMPLATES["default"])
            return template.format(message=message)
    
    def format_conversation(
        self,
        messages: List[Dict[str, str]], 
        model_id: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """Format a multi-turn conversation."""
        model_type = self.detect_model_type(model_id)
        
        if model_type == "mistral":
            return self._format_mistral_conversation(messages, system_prompt)
        elif model_type == "llama":
            return self._format_llama_conversation(messages, system_prompt)
        elif model_type == "qwen":
            return self._format_qwen_conversation(messages, system_prompt)
        elif model_type == "gemma":
            return self._format_gemma_conversation(messages, system_prompt)
        else:
            return self._format_default_conversation(messages, system_prompt)
    
    def _format_mistral_conversation(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Format conversation for Mistral models."""
        formatted = "<s>"
        
        for i, msg in enumerate(messages):
            if msg["role"] == "user":
                if i == 0 and system_prompt:
                    formatted += f"[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{msg['content']} [/INST]"
                else:
                    formatted += f"[INST] {msg['content']} [/INST]"
            elif msg["role"] == "assistant":
                formatted += f" {msg['content']} </s>"
        
        return formatted
    
    def _format_llama_conversation(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Format conversation for Llama models."""
        formatted = ""
        
        if system_prompt:
            formatted += f"### System: {system_prompt}\n"
        
        for msg in messages:
            if msg["role"] == "user":
                formatted += f"### Human: {msg['content']}\n"
            elif msg["role"] == "assistant":
                formatted += f"### Assistant: {msg['content']}\n"
        
        formatted += "### Assistant:"
        return formatted
    
    def _format_qwen_conversation(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Format conversation for Qwen models."""
        formatted = ""
        
        if system_prompt:
            formatted += f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        
        for msg in messages:
            role = msg["role"]
            if role == "assistant":
                role = "assistant"
            formatted += f"<|im_start|>{role}\n{msg['content']}<|im_end|>\n"
        
        formatted += "<|im_start|>assistant\n"
        return formatted
    
    def _format_gemma_conversation(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Format conversation for Gemma models."""
        formatted = ""
        
        if system_prompt:
            formatted += f"<start_of_turn>system\n{system_prompt}<end_of_turn>\n"
        
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            formatted += f"<start_of_turn>{role}\n{msg['content']}<end_of_turn>\n"
        
        formatted += "<start_of_turn>model\n"
        return formatted
    
    def _format_default_conversation(
        self, 
        messages: List[Dict[str, str]], 
        system_prompt: Optional[str] = None
    ) -> str:
        """Format conversation for generic models."""
        formatted = ""
        
        if system_prompt:
            formatted += f"System: {system_prompt}\n\n"
        
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n"
        
        formatted += "Assistant:"
        return formatted


# Global formatter instance
prompt_formatter = PromptFormatter()


def format_prompt(
    message: str, 
    model_id: str,
    system_prompt: Optional[str] = None
) -> str:
    """Format a single prompt."""
    return prompt_formatter.format_prompt(message, model_id, system_prompt)


def format_conversation(
    messages: List[Dict[str, str]], 
    model_id: str,
    system_prompt: Optional[str] = None
) -> str:
    """Format a multi-turn conversation."""
    return prompt_formatter.format_conversation(messages, model_id, system_prompt)