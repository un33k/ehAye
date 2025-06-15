"""Main Ali CLI entry point with subcommands using Click with Typer integration."""

import sys
import os
import logging
import click
import subprocess
from rich.console import Console

# Import subcommand CLIs
from .ollama_cli import cli as ollama_cli, main as ollama_main
from .base import handle_keyboard_interrupt
from ..core.logging import ehaye_logger

console = Console()

def check_virtualenv():
    """Check if running in local virtual environment."""
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path or '.venv' not in venv_path:
        console.print("[red]Error: Must run from local virtual environment.[/red]")
        console.print("[yellow]Run: deactivate >/dev/null 2>&1 || source .venv/bin/activate[/yellow]")
        sys.exit(1)

@click.group(name="ali", help="Ali - Artificial Line Interface for ehAye Local", invoke_without_command=True)
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

# Add Click-based Ollama CLI
cli.add_command(ollama_cli, name="olla")

# Simple delegate commands for Typer-based CLIs
@cli.command(name="mod", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def mod_delegate(ctx):
    """Model management"""
    # Convert Click args to model_cli flags
    args = ["python", "-m", "ali.cli.model_cli"]
    
    # Map common commands to flags
    if ctx.args and ctx.args[0] == "list":
        args.append("-l")
        args.extend(ctx.args[1:])  # Add any additional args
    elif ctx.args and ctx.args[0] == "search":
        args.append("-s")
        args.extend(ctx.args[1:])
    elif ctx.args and ctx.args[0] == "download":
        args.append("-d")
        args.extend(ctx.args[1:])
    elif ctx.args and ctx.args[0] == "remove":
        args.append("-r")
        args.extend(ctx.args[1:])
    elif ctx.args and ctx.args[0] == "info":
        args.append("-i")
        args.extend(ctx.args[1:])
    else:
        # Pass through all args as-is for flag-based usage
        args.extend(ctx.args)
    
    result = subprocess.run(args)
    ctx.exit(result.returncode)

@cli.command(name="chat", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context  
def chat_delegate(ctx):
    """Chat interface"""
    args = ["python", "-m", "ali.cli.chat_cli"] + ctx.args
    result = subprocess.run(args)
    ctx.exit(result.returncode)

@cli.command(name="perf", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def perf_delegate(ctx):
    """Performance benchmarking"""
    args = ["python", "-m", "ali.cli.benchmark_cli"] + ctx.args
    result = subprocess.run(args)  
    ctx.exit(result.returncode)

@cli.command(name="sys", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def sys_delegate(ctx):
    """System management"""
    args = ["python", "-m", "ali.cli.system_cli"] + ctx.args
    result = subprocess.run(args)
    ctx.exit(result.returncode)

def main():
    """Main entry point for Ali CLI."""
    # Check virtual environment first
    check_virtualenv()
    
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