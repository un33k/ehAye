"""Ollama CLI interface using Click."""

import sys
import subprocess
import time

import click
from rich.console import Console
from rich.status import Status

from ..core.logging import get_logger
from .base import handle_keyboard_interrupt, show_error, show_info, show_success

console = Console()
logger = get_logger("cli.ollama")


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_ollama_service() -> bool:
    """Start Ollama service if not running."""
    if check_ollama():
        show_success("Ollama is already running")
        return True
    
    show_info("Starting Ollama service...")
    try:
        # Try to start via brew services
        result = subprocess.run(
            ["brew", "services", "start", "ollama"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Wait for service to start
            with Status("Starting Ollama service...", console=console):
                for _ in range(10):
                    time.sleep(1)
                    if check_ollama():
                        show_success("Ollama service started")
                        return True
            
        show_info("Failed to start via brew services, trying direct launch...")
        # Try direct launch in background
        subprocess.Popen(
            ["ollama", "serve"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        
        # Wait for service to start
        with Status("Starting Ollama service...", console=console):
            for _ in range(10):
                time.sleep(1)
                if check_ollama():
                    show_success("Ollama service started")
                    return True
        
        show_error("Failed to start Ollama service")
        return False
        
    except Exception as e:
        show_error(f"Error starting Ollama: {e}")
        return False


@click.group(name="olla", help="Direct Ollama operations", invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Main Ollama CLI group."""
    # If no subcommand was invoked, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def start():
    """Start Ollama service."""
    try:
        start_ollama_service()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Failed to start Ollama: {e}")


@cli.command()
def stop():
    """Stop Ollama service."""
    try:
        show_info("Stopping Ollama service...")
        result = subprocess.run(
            ["brew", "services", "stop", "ollama"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            show_success("Ollama service stopped")
        else:
            show_error("Failed to stop Ollama service")
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error stopping Ollama: {e}")


@cli.command()
def list():
    """List available Ollama models."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            console.print("📦 Available Ollama Models:")
            console.print(result.stdout)
        else:
            show_error("Failed to list models")
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error listing models: {e}")


@cli.command()
def ps():
    """Show running Ollama processes."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        result = subprocess.run(
            ["ollama", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            console.print("🔄 Running Ollama Processes:")
            console.print(result.stdout)
        else:
            show_error("Failed to show running processes")
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error showing processes: {e}")


@cli.command()
@click.argument('model')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def pull(model, verbose):
    """Download a model via Ollama."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        show_info(f"Downloading {model} via Ollama...")
        
        if verbose:
            # Show full output
            result = subprocess.run(["ollama", "pull", model])
        else:
            # Capture output and show progress
            process = subprocess.Popen(
                ["ollama", "pull", model],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            with Status(f"Pulling {model}...", console=console) as status:
                if process.stdout:
                    for line in process.stdout:
                        line = line.strip()
                        if line and ("pulling" in line.lower() or "%" in line):
                            # Update status with progress info
                            status.update(f"Pulling {model}: {line}")
            
            process.wait()
            result = process
        
        if result.returncode == 0:
            show_success(f"Successfully downloaded {model}")
        else:
            show_error(f"Failed to download {model}")
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error downloading model: {e}")


@cli.command()
@click.argument('model')
def run(model):
    """Run a model interactively via Ollama."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        console.print(f"🤖 Starting chat with {model} via Ollama...")
        console.print("Type '/bye' or press Ctrl+C to quit")
        console.print("-" * 60)
        
        subprocess.run(["ollama", "run", model])
        
    except KeyboardInterrupt:
        console.print("\n👋 Chat session ended")
    except Exception as e:
        show_error(f"Error running model: {e}")


@cli.command()
@click.argument('model')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
def remove(model, force):
    """Remove a model from Ollama."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        if not force:
            if not click.confirm(f"Remove model {model}?"):
                return
        
        show_info(f"Removing {model}...")
        result = subprocess.run(
            ["ollama", "rm", model],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            show_success(f"Successfully removed {model}")
        else:
            show_error(f"Failed to remove {model}: {result.stderr}")
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error removing model: {e}")


@cli.command()
@click.argument('model', required=False)
def info(model):
    """Show Ollama model information."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        if model:
            result = subprocess.run(
                ["ollama", "show", model],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                console.print(f"📋 Model Information: {model}")
                console.print("=" * 60)
                console.print(result.stdout)
            else:
                show_error(f"Failed to show info for {model}")
        else:
            # Show general Ollama info
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                console.print("🦙 Ollama Information:")
                console.print("=" * 30)
                console.print(f"Version: {result.stdout.strip()}")
                console.print(f"Status: {'Running' if check_ollama() else 'Stopped'}")
            else:
                show_error("Failed to get Ollama info")
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error getting info: {e}")


@cli.command()
def help():
    """Show Ollama help."""
    try:
        subprocess.run(["ollama", "--help"])
    except Exception as e:
        show_error(f"Error showing Ollama help: {e}")


@cli.command()
def serve():
    """Start Ollama server directly."""
    try:
        subprocess.run(["ollama", "serve"])
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error starting Ollama server: {e}")


@cli.command()
@click.argument('args', nargs=-1, required=True)
def create(args):
    """Create a model from a Modelfile."""
    try:
        subprocess.run(["ollama", "create"] + list(args))
    except Exception as e:
        show_error(f"Error creating model: {e}")


@cli.command()
@click.argument('model')
def show(model):
    """Show information for a model (same as 'info' but matching Ollama)."""
    try:
        subprocess.run(["ollama", "show", model])
    except Exception as e:
        show_error(f"Error showing model info: {e}")


def main():
    """Main entry point with -- passthrough handling."""
    # Handle -- passthrough BEFORE Click processes anything
    if '--' in sys.argv:
        try:
            dash_index = sys.argv.index('--')
            ollama_args = sys.argv[dash_index + 1:]
            
            if not ollama_args:
                console.print("Usage: ali olla -- <ollama_args>")
                console.print("Examples:")
                console.print("  ali olla -- --help")
                console.print("  ali olla -- --version")
                console.print("  ali olla -- create mymodel -f Modelfile")
                sys.exit(0)
            
            # Run ollama directly with the provided arguments
            result = subprocess.run(["ollama"] + ollama_args)
            sys.exit(result.returncode)
            
        except KeyboardInterrupt:
            handle_keyboard_interrupt()
        except Exception as e:
            show_error(f"Error running ollama command: {e}")
            sys.exit(1)
    
    # If no --, proceed with normal Click processing
    try:
        cli()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)

# Create a Typer-compatible wrapper for integration with existing main CLI
import typer
app = typer.Typer(name="olla", help="Direct Ollama operations")

@app.callback(invoke_without_command=True)
def typer_wrapper(ctx: typer.Context):
    """Typer wrapper for compatibility."""
    # If no subcommand was invoked, show help
    if ctx.invoked_subcommand is None:
        console.print("Use 'ali olla --help' for available commands or 'ali olla -- <ollama_args>' for direct passthrough")

# Add basic commands as Typer wrappers
@app.command()
def start():
    """Start Ollama service."""
    try:
        start_ollama_service()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Failed to start Ollama: {e}")

@app.command()
def list():
    """List available Ollama models."""
    try:
        if not start_ollama_service():
            return
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print("📦 Available Ollama Models:")
            console.print(result.stdout)
        else:
            show_error("Failed to list models")
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error listing models: {e}")

@app.command()
def ps():
    """Show running Ollama processes."""
    try:
        if not start_ollama_service():
            return
        result = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print("🔄 Running Ollama Processes:")
            console.print(result.stdout)
        else:
            show_error("Failed to show running processes")
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        show_error(f"Error showing processes: {e}")

if __name__ == "__main__":
    main()