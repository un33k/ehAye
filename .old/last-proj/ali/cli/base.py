"""Base CLI functionality and common utilities."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..core.config import get_config, load_config
from ..core.environment import EnvironmentValidator
from ..core.exceptions import EhAyeError
from ..core.logging import get_logger, ehaye_logger

console = Console()
logger = get_logger("cli")


class BaseCLI:
    """Base class for all CLI commands."""
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.app = typer.Typer(
            name=app_name,
            help=f"ehAye Local {app_name.title()} Interface",
            add_completion=False
        )
        self.config = None
        self.validator = EnvironmentValidator()
    
    def setup_logging(self, verbose: bool = False, quiet: bool = False) -> None:
        """Setup logging based on CLI flags."""
        if quiet:
            level = "ERROR"
        elif verbose:
            level = "DEBUG"
        else:
            level = "INFO"
        
        log_file = None
        if self.config:
            log_file = self.config.paths.logs_dir / f"{self.app_name}.log"
        
        ehaye_logger.setup(level=level, log_file=log_file, enable_rich=not quiet)
    
    def load_configuration(self, config_file: Optional[Path] = None) -> None:
        """Load application configuration."""
        try:
            self.config = load_config(config_file)
            self.config.setup_environment()
            logger.debug("Configuration loaded successfully")
        except Exception as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            if "config" in str(e).lower():
                console.print("[yellow]Tip: Create config/settings.toml or use default configuration[/yellow]")
            raise typer.Exit(1)
    
    def validate_environment(self, skip_venv: bool = False) -> None:
        """Validate runtime environment."""
        try:
            if not skip_venv:
                self.validator.check_virtual_environment()
            
            self.validator.validate_python_version()
            self.validator.validate_system_resources()
            
            logger.debug("Environment validation passed")
            
        except Exception as e:
            console.print(f"[red]Environment error: {e}[/red]")
            
            if "virtual environment" in str(e):
                console.print("[yellow]Run: source .venv/bin/activate[/yellow]")
            elif "Python" in str(e):
                console.print("[yellow]Ensure Python 3.10+ is installed[/yellow]")
            
            raise typer.Exit(1)
    
    def handle_error(self, error: Exception) -> None:
        """Handle and display errors appropriately."""
        if isinstance(error, EhAyeError):
            console.print(f"[red]Error: {error.message}[/red]")
            if error.code:
                console.print(f"[dim]Error code: {error.code}[/dim]")
        else:
            console.print(f"[red]Unexpected error: {error}[/red]")
            logger.error(f"Unexpected error in {self.app_name}: {error}", exc_info=True)
        
        raise typer.Exit(1)
    
    def add_common_options(self, callback):
        """Decorator to add common CLI options."""
        callback = typer.Option(
            False, "--verbose", "-v", 
            help="Enable verbose logging"
        )(callback)
        
        callback = typer.Option(
            False, "--quiet", "-q", 
            help="Suppress output except errors"
        )(callback)
        
        callback = typer.Option(
            None, "--config", "-c", 
            help="Custom configuration file path"
        )(callback)
        
        return callback


def common_setup(
    ctx: typer.Context,
    verbose: bool = False,
    quiet: bool = False,
    config: Optional[Path] = None,
    skip_venv: bool = False
) -> BaseCLI:
    """Common setup for all CLI commands."""
    # Get CLI instance from context
    cli = ctx.find_root().info_name
    base_cli = BaseCLI(cli)
    
    # Setup logging first
    base_cli.setup_logging(verbose, quiet)
    
    # Load configuration
    base_cli.load_configuration(config)
    
    # Validate environment
    base_cli.validate_environment(skip_venv)
    
    return base_cli


def handle_keyboard_interrupt():
    """Handle Ctrl+C gracefully."""
    console.print("\n[yellow]Operation cancelled by user[/yellow]")
    raise typer.Exit(0)


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    return typer.confirm(message, default=default)


def show_success(message: str) -> None:
    """Show success message."""
    console.print(f"[green]✅ {message}[/green]")


def show_warning(message: str) -> None:
    """Show warning message."""
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def show_error(message: str) -> None:
    """Show error message."""
    console.print(f"[red]❌ {message}[/red]")


def show_info(message: str) -> None:
    """Show info message."""
    console.print(f"[blue]ℹ️  {message}[/blue]")