"""Ollama CLI interface."""

import sys
import subprocess
import time
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.status import Status

from ..core.logging import get_logger
from .base import handle_keyboard_interrupt, show_error, show_info, show_success

app = typer.Typer(name="ollama", help="Direct Ollama operations")
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


@app.command()
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


@app.command()
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


@app.command()
def pull(
    model: str = typer.Argument(..., help="Model name to download"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
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


@app.command()
def run(
    model: str = typer.Argument(..., help="Model name to run"),
):
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


@app.command()
def remove(
    model: str = typer.Argument(..., help="Model name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Remove a model from Ollama."""
    try:
        # Ensure service is running
        if not start_ollama_service():
            return
            
        if not force:
            if not typer.confirm(f"Remove model {model}?"):
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


@app.command()
def info(
    model: Optional[str] = typer.Argument(None, help="Model name to show info for")
):
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


def main():
    """Main entry point for Ollama CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()