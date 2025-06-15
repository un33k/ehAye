"""Main Ali CLI entry point with subcommands."""

import typer
from rich.console import Console

# Import subcommand apps
from .model_cli_typer import app as models_app
from .chat_cli import app as chat_app  
from .benchmark_cli import app as benchmark_app
from .system_cli import app as system_app
from .ollama_cli import app as ollama_app
from .base import handle_keyboard_interrupt

app = typer.Typer(
    name="ali",
    help="Ali - Artificial Line Interface for ehAye Local",
    no_args_is_help=True
)
console = Console()

# Add subcommands
app.add_typer(models_app, name="mod", help="Model management")
app.add_typer(chat_app, name="chat", help="Chat interface") 
app.add_typer(benchmark_app, name="perf", help="Performance benchmarking")
app.add_typer(system_app, name="sys", help="System management")
app.add_typer(ollama_app, name="ollama", help="Direct Ollama operations")

def main():
    """Main entry point for Ali CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()