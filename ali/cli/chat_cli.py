"""Chat interface CLI."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..logging.logger import get_logger
# Placeholder imports - actual implementation will be added later
# from ..chat.session import ChatSession, create_chat_session
# from ..generation.parameters import GenerationConfig  
# from ..chat.streaming import stream_to_console
# from ..models.registry import get_installed_models, search_models
from .base import BaseCLI, common_setup, handle_keyboard_interrupt, show_error, show_info

# Placeholder classes for missing dependencies
class GenerationConfig:
    def __init__(self, max_tokens=512, temperature=0.7):
        self.max_tokens = max_tokens
        self.temperature = temperature

class ChatSession:
    def __init__(self, model_id, config, system_prompt=None):
        self.model_id = model_id
        self.generation_config = config
        self.conversation = type('obj', (object,), {'system_prompt': system_prompt, 'messages': []})()
    
    def send_message(self, message, streaming=True):
        return "This is a placeholder response. Chat functionality not yet implemented."
    
    def clear_conversation(self):
        self.conversation.messages = []
    
    def save_conversation(self):
        pass

def create_chat_session(model_id, config, system_prompt=None):
    return "session_id_placeholder"

def get_chat_session(session_id):
    return ChatSession("placeholder_model", GenerationConfig())

def stream_to_console(response_stream, prefix):
    console.print(f"{prefix}{response_stream}")

def get_installed_models():
    return [type('obj', (object,), {'id': 'placeholder_model', 'display_name': 'Placeholder Model', 'category': 'test'})()]

def search_models(query=None):
    return get_installed_models()

def get_chat_command_prefix():
    """Get the chat command prefix from config."""
    try:
        from ..configuration import get_config
        config = get_config()
        main_cmd = config.cli.main_command
        chat_cmd = config.cli.chat_command
        return f"{main_cmd} {chat_cmd}"
    except Exception:
        return "ali chat"

@click.group(name="chat")
def app():
    """Interactive chat with LLM models"""
    pass
console = Console()
logger = get_logger("cli.chat")


@app.command()
@click.option("--model", "-m", help="Model to use for chat")
@click.option("--temp", "-t", default=0.7, help="Generation temperature")
@click.option("--tokens", default=512, help="Maximum tokens per response")
@click.option("--system", "-s", help="System prompt")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def interactive(ctx, model, temp, tokens, system, no_stream, verbose, quiet, config):
    """Start an interactive chat session."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Select model if not provided
        if not model:
            model = select_model_interactive()
            if not model:
                return
        
        # Create generation config
        gen_config = GenerationConfig(
            max_tokens=tokens,
            temperature=temp
        )
        
        # Create chat session
        session_id = create_chat_session(model, gen_config, system)
        
        # Start chat loop
        start_chat_loop(session_id, streaming=not no_stream)
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.argument("prompt")
@click.option("--model", "-m", help="Model to use")
@click.option("--temp", "-t", default=0.7, help="Generation temperature")
@click.option("--tokens", default=512, help="Maximum tokens per response")
@click.option("--system", "-s", help="System prompt")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def single(ctx, prompt, model, temp, tokens, system, no_stream, verbose, quiet, config):
    """Send a single prompt and get response."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Select model if not provided
        if not model:
            model = select_model_interactive()
            if not model:
                return
        
        # Create generation config
        gen_config = GenerationConfig(
            max_tokens=tokens,
            temperature=temp
        )
        
        # Create chat session
        session = ChatSession(model, gen_config, system)
        
        # Send single message
        console.print(f"[blue]🧑 User:[/blue] {prompt}")
        
        if no_stream:
            response = session.send_message(prompt, streaming=False)
            console.print(f"[green]🤖 Assistant:[/green] {response}")
        else:
            response_stream = session.send_message(prompt, streaming=True)
            stream_to_console(response_stream, "🤖 Assistant: ")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.option("--search", "-s", help="Search models")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def models(ctx, search, verbose, quiet, config):
    """List available models for chat."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        if search:
            models = search_models(query=search)
        else:
            models = get_installed_models()
        
        if not models:
            show_error("No models found")
            return
        
        console.print("📋 Available Models:")
        console.print("=" * 50)
        
        for i, model in enumerate(models, 1):
            console.print(f"  {i:2d}. {model.display_name}")
            if verbose:
                console.print(f"      ID: {model.id}")
                console.print(f"      Category: {model.category}")
        
        console.print(f"\n💡 Use: ali chat interactive --model <model_id>")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


def select_model_interactive() -> Optional[str]:
    """Interactive model selection."""
    models = get_installed_models()
    
    if not models:
        show_error("No models found. Install models first using: ali download")
        return None
    
    console.print("🤖 Available Models:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        console.print(f"  {i:2d}. {model.display_name}")
    
    try:
        choice = click.prompt("\nSelect model number", type=int)
        
        if 1 <= choice <= len(models):
            selected = models[choice - 1]
            show_info(f"Selected: {selected.display_name}")
            return selected.id
        else:
            show_error("Invalid selection")
            return None
            
    except (ValueError, click.Abort):
        return None


def start_chat_loop(session_id: str, streaming: bool = True) -> None:
    """Start the interactive chat loop."""
    from ..chat.session import get_chat_session
    
    session = get_chat_session(session_id)
    if not session:
        show_error("Failed to create chat session")
        return
    
    console.print("\n💬 Chat Session Started")
    console.print("🎮 Commands: 'quit', 'clear', 'help', 'settings'")
    console.print("-" * 60)
    
    try:
        while True:
            try:
                user_input = console.input("\n[blue]🧑 You:[/blue] ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'clear':
                    session.clear_conversation()
                    console.print("🧹 Conversation cleared")
                    continue
                elif user_input.lower() == 'help':
                    show_chat_help()
                    continue
                elif user_input.lower() == 'settings':
                    show_chat_settings(session)
                    continue
                
                # Generate response
                if streaming:
                    response_stream = session.send_message(user_input, streaming=True)
                    stream_to_console(response_stream, "🤖 Assistant: ")
                else:
                    response = session.send_message(user_input, streaming=False)
                    console.print(f"[green]🤖 Assistant:[/green] {response}")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
                continue
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                show_error(f"Chat error: {e}")
                continue
    
    finally:
        # Save conversation
        session.save_conversation()
        console.print("[dim]💾 Conversation saved[/dim]")


def show_chat_help() -> None:
    """Show chat help."""
    console.print("""
💡 Available Commands:
  quit, exit, q    - Exit the chat
  clear           - Clear conversation history
  help            - Show this help
  settings        - Show current settings
  
🎮 Tips:
  - Use Ctrl+C to interrupt generation
  - Multi-line prompts are supported
  - Conversation history is automatically saved
""")


def show_chat_settings(session: ChatSession) -> None:
    """Show current chat settings."""
    config = session.generation_config
    console.print(f"""
⚙️ Current Settings:
  Model: {session.model_id}
  Temperature: {config.temperature}
  Max Tokens: {config.max_tokens}
  System Prompt: {session.conversation.system_prompt or 'None'}
  Messages: {len(session.conversation.messages)}
""")


def main():
    """Main entry point for chat CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()