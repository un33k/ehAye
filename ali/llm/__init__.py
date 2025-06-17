"""LLM module for ehAye - chat, generation, prompts, and streaming functionality."""

from .chat import (
    Conversation,
    ChatSession,
    ChatManager,
    chat_manager,
    create_chat_session,
    get_chat_session,
)

from .generation import (
    GenerationConfig,
    TextGenerator,
    text_generator,
    generate_text,
    generate_text_stream,
    create_generation_config,
)

from .prompts import (
    PromptFormatter,
    prompt_formatter,
    format_prompt,
    format_conversation,
)

from .streaming import (
    StreamHandler,
    BufferedStreamHandler,
    stream_handler,
    buffered_handler,
    stream_to_console,
    stream_with_markdown,
)

__all__ = [
    # Chat functionality
    "Conversation",
    "ChatSession", 
    "ChatManager",
    "chat_manager",
    "create_chat_session",
    "get_chat_session",
    
    # Generation functionality
    "GenerationConfig",
    "TextGenerator",
    "text_generator",
    "generate_text",
    "generate_text_stream",
    "create_generation_config",
    
    # Prompt formatting
    "PromptFormatter",
    "prompt_formatter",
    "format_prompt",
    "format_conversation",
    
    # Streaming functionality
    "StreamHandler",
    "BufferedStreamHandler",
    "stream_handler",
    "buffered_handler",
    "stream_to_console",
    "stream_with_markdown",
]