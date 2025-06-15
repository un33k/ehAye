"""Main Ali CLI entry point with subcommands using Click."""

import sys
import logging
import click
from rich.console import Console

# Import subcommand CLIs
from .ollama_cli import cli as ollama_cli, main as ollama_main
from .model_cli_typer import app as models_app
from .chat_cli import app as chat_app  
from .benchmark_cli import app as benchmark_app
from .system_cli import app as system_app
from .base import handle_keyboard_interrupt
from ..core.logging import ehaye_logger

console = Console()

@click.group(name="ali", help="Ali - Artificial Line Interface", invoke_without_command=True)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--debug', '-d', is_flag=True, help='Enable debug output')
@click.pass_context
def cli(ctx, verbose, debug):
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

# Add subcommands by importing and adding them
cli.add_command(ollama_cli, name="olla")

# Wrapper commands that delegate to Typer apps
@cli.command(name="mod", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def mod_wrapper(ctx):
    """Model management commands."""
    import sys
    # Reconstruct sys.argv for the Typer app
    original_argv = sys.argv
    try:
        # Create argv for the typer app: [script_name, subcommand, *extra_args]
        sys.argv = [sys.argv[0], "mod"] + ctx.args
        models_app()
    finally:
        sys.argv = original_argv

@cli.command(name="chat", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def chat_wrapper(ctx):
    """Chat interface commands."""
    import sys
    original_argv = sys.argv
    try:
        sys.argv = [sys.argv[0], "chat"] + ctx.args
        chat_app()
    finally:
        sys.argv = original_argv

@cli.command(name="perf", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def perf_wrapper(ctx):
    """Performance benchmarking commands."""
    import sys
    original_argv = sys.argv
    try:
        sys.argv = [sys.argv[0], "perf"] + ctx.args
        benchmark_app()
    finally:
        sys.argv = original_argv

@cli.command(name="sys", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def sys_wrapper(ctx):
    """System management commands."""
    import sys
    original_argv = sys.argv
    try:
        sys.argv = [sys.argv[0], "sys"] + ctx.args
        system_app()
    finally:
        sys.argv = original_argv

def main():
    """Main entry point for Ali CLI."""
    # Special handling for ollama -- passthrough
    if len(sys.argv) >= 3 and sys.argv[1] == "olla" and "--" in sys.argv:
        # Extract just the olla part and delegate to ollama_main
        olla_index = sys.argv.index("olla")
        sys.argv = sys.argv[olla_index:]  # Remove 'ali' from argv
        ollama_main()
        return
    
    try:
        cli()
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