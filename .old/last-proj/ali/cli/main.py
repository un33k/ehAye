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

def run_delegate_command(module_name, default_subcommand, ctx_args, valid_subcommands=None):
    """Helper function to run delegate commands with proper error handling."""
    args = ["python", "-m", f"ali.cli.{module_name}"]
    
    if not ctx_args:
        # No args provided, use default subcommand
        args.append(default_subcommand)
    else:
        # If first arg is a flag, prepend default subcommand
        if ctx_args[0].startswith('-'):
            args.extend([default_subcommand] + list(ctx_args))
        # If first arg is a known subcommand, pass through
        elif valid_subcommands and ctx_args[0] in valid_subcommands:
            args.extend(ctx_args)
        # Otherwise, prepend default subcommand
        else:
            args.extend([default_subcommand] + list(ctx_args))
    
    result = subprocess.run(args, capture_output=True, text=True)
    
    # Clean up error messages
    if result.returncode != 0 and result.stderr:
        error_output = result.stderr
        # Replace internal module references
        error_output = error_output.replace(f'python -m ali.cli.{module_name}', f'ali {module_name.replace("_cli", "")}')
        # Filter out tracebacks
        error_lines = error_output.split('\n')
        clean_lines = [line for line in error_lines if not line.strip().startswith('Traceback') and not line.strip().startswith('File ')]
        if clean_lines:
            print('\n'.join(clean_lines), file=sys.stderr)
    elif result.stdout:
        console.print(result.stdout)
    
    return result.returncode

def check_virtualenv():
    """Check if running in local virtual environment."""
    venv_path = os.environ.get('VIRTUAL_ENV')
    if not venv_path or '.venv' not in venv_path:
        console.print("[red]Error: Must run from local virtual environment.[/red]")
        console.print("[yellow]Run: deactivate >/dev/null 2>&1 || source .venv/bin/activate[/yellow]")
        sys.exit(1)

@click.group(name="ali", help="Ali - Artificial Line Interface for ehAye", invoke_without_command=True)
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
    # Model CLI uses flags, so special handling needed
    args = ["python", "-m", "ali.cli.model_cli"]
    
    if not ctx.args:
        # Default to list
        args.append("-l")
    else:
        # Map common commands to flags
        if ctx.args[0] == "list":
            args.append("-l")
            args.extend(ctx.args[1:])
        elif ctx.args[0] == "search":
            args.append("-s")
            args.extend(ctx.args[1:])
        elif ctx.args[0] == "download":
            args.append("-d")
            args.extend(ctx.args[1:])
        elif ctx.args[0] == "remove":
            args.append("-r")
            args.extend(ctx.args[1:])
        elif ctx.args[0] == "info":
            args.append("-i")
            args.extend(ctx.args[1:])
        else:
            # Pass through all args as-is for flag-based usage
            args.extend(ctx.args)
    
    result = subprocess.run(args, capture_output=True, text=True)
    
    # Clean up error messages
    if result.returncode != 0 and result.stderr:
        error_output = result.stderr.replace('python -m ali.cli.model_cli', 'ali mod')
        error_lines = error_output.split('\n')
        clean_lines = [line for line in error_lines if not line.strip().startswith('Traceback') and not line.strip().startswith('File ')]
        if clean_lines:
            print('\n'.join(clean_lines), file=sys.stderr)
    elif result.stdout:
        console.print(result.stdout)
    
    ctx.exit(result.returncode)

@cli.command(name="chat", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context  
def chat_delegate(ctx):
    """Chat interface"""
    # Check for common mistakes and show helpful error
    if ctx.args and ctx.args[0] in ['-l', '--list']:
        console.print("[red]Error: -l/--list is not a valid option for chat.[/red]")
        console.print("[yellow]Did you mean: ali mod list[/yellow]")
        ctx.exit(1)
    
    valid_subcommands = ['interactive', 'single', 'models']
    args = ["python", "-m", "ali.cli.chat_cli"]
    
    if not ctx.args:
        # Default to interactive
        args.append("interactive")
    elif ctx.args[0].startswith('-'):
        # If first arg is a flag, assume interactive mode
        args.extend(['interactive'] + list(ctx.args))
    elif ctx.args[0] in valid_subcommands:
        # Known subcommand, pass through
        args.extend(ctx.args)
    else:
        # Assume it's a prompt for single mode
        args.extend(['single'] + list(ctx.args))
    
    result = subprocess.run(args, capture_output=True, text=True)
    
    # Clean up error messages
    if result.returncode != 0 and result.stderr:
        error_output = result.stderr.replace('python -m ali.cli.chat_cli', 'ali chat')
        error_lines = error_output.split('\n')
        clean_lines = [line for line in error_lines if not line.strip().startswith('Traceback') and not line.strip().startswith('File ')]
        if clean_lines:
            print('\n'.join(clean_lines), file=sys.stderr)
    elif result.stdout:
        console.print(result.stdout)
    
    ctx.exit(result.returncode)

@cli.command(name="perf", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def perf_delegate(ctx):
    """Performance benchmarking"""
    valid_subcommands = ['single', 'compare', 'list-models', 'validate']
    returncode = run_delegate_command('benchmark_cli', 'single', ctx.args, valid_subcommands)
    ctx.exit(returncode)

@cli.command(name="sys", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@click.pass_context
def sys_delegate(ctx):
    """System management"""
    valid_subcommands = ['info', 'validate', 'config', 'setup', 'cleanup']
    returncode = run_delegate_command('system_cli', 'info', ctx.args, valid_subcommands)
    ctx.exit(returncode)

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