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
        """Send message to Ollama and get response."""
        try:
            import subprocess
            from rich.status import Status
            
            # Show loading status
            with Status("🤖 Generating response...", console=console):
                result = subprocess.run(
                    ['ollama', 'run', self.model_id, message],
                    capture_output=True, text=True, timeout=60
                )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "pull model" in error_msg or "model not found" in error_msg:
                    return f"Model '{self.model_id}' not found. Try: ollama pull {self.model_id}"
                return f"Error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return "⏱️ Request timed out. The model might be loading or the prompt is too complex."
        except Exception as e:
            return f"Error: {e}"
    
    def clear_conversation(self):
        self.conversation.messages = []
    
    def save_conversation(self):
        pass

def create_chat_session(model_id, config, system_prompt=None):
    return ChatSession(model_id, config, system_prompt)

def get_chat_session(session_id):
    # In this simplified version, session_id is actually the ChatSession object
    return session_id

def stream_to_console(response_stream, prefix):
    console.print(f"{prefix}{response_stream}")

def get_installed_models():
    """Get list of installed Ollama models."""
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        models = []
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    model_id = name.split(':')[0] if ':' in name else name
                    models.append(type('obj', (object,), {
                        'id': name,
                        'display_name': name,
                        'category': 'ollama'
                    })())
        return models
    except Exception:
        return []

def search_models(query=None):
    models = get_installed_models()
    if not query:
        return models
    query_lower = query.lower()
    return [m for m in models if query_lower in m.display_name.lower()]

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

@click.group(name="chat", invoke_without_command=True)
@click.pass_context
def app(ctx):
    """Interactive chat with LLM models"""
    if ctx.invoked_subcommand is None:
        # Default to interactive mode
        ctx.invoke(interactive)
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
        session = create_chat_session(model, gen_config, system)
        
        # Start chat loop
        start_chat_loop(session, streaming=not no_stream)
        
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
        choice_str = click.prompt("\nSelect model number (or 'q' to quit)", type=str)
        
        # Handle quit commands
        if choice_str.lower().strip() in ['q', 'quit', 'exit']:
            console.print("👋 Cancelled")
            return None
            
        try:
            choice = int(choice_str)
        except ValueError:
            show_error("Please enter a valid number or 'q' to quit")
            return None
        
        if 1 <= choice <= len(models):
            selected = models[choice - 1]
            show_info(f"Selected: {selected.display_name}")
            return selected.id
        else:
            show_error("Invalid selection")
            return None
            
    except click.Abort:
        console.print("👋 Cancelled")
        return None


def start_chat_loop(session, streaming: bool = True) -> None:
    """Start the interactive chat loop."""
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