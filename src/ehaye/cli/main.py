"""Main Ali CLI entry point with subcommands."""

import sys
import logging
import typer
from rich.console import Console

# Import subcommand apps
from .model_cli_typer import app as models_app
from .chat_cli import app as chat_app  
from .benchmark_cli import app as benchmark_app
from .system_cli import app as system_app
from .ollama_cli import app as ollama_app
from .base import handle_keyboard_interrupt
from ..core.logging import ehaye_logger

app = typer.Typer(
    name="ali",
    help="Ali - Artificial Line Interface for ehAye Local",
    no_args_is_help=False,  # We handle this manually in callback
    add_completion=True,
    pretty_exceptions_show_locals=False
)
console = Console()

# Global verbose/debug flag
verbose_option = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
debug_option = typer.Option(False, "--debug", "-d", help="Enable debug output")

# Add subcommands
app.add_typer(models_app, name="mod", help="Model management")
app.add_typer(chat_app, name="chat", help="Chat interface") 
app.add_typer(benchmark_app, name="perf", help="Performance benchmarking")
app.add_typer(system_app, name="sys", help="System management")
app.add_typer(ollama_app, name="olla", help="Direct Ollama operations")

@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    verbose: bool = verbose_option,
    debug: bool = debug_option
):
    """Configure global options."""
    # Set up logging based on flags
    if debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"
    
    # Configure the logger
    ehaye_logger.setup(level=log_level, enable_rich=True)
    
    # Also set the root logger to prevent other modules from logging
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # If no command was given, just show help without error
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)

def main():
    """Main entry point for Ali CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except SystemExit:
        # Just pass through system exits (help, etc)
        pass
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()