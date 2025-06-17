"""Base CLI functionality and common utilities."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from ..configuration import get_config, load_config
from ..exceptions import EhAyeError
from ..logging.logger import get_logger, ehaye_logger

console = Console()
logger = get_logger("cli")


class BaseCLI:
    """Base class for all CLI commands."""
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.config = None
    
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
            raise click.ClickException(str(e))
    
    def validate_environment(self, skip_venv: bool = False) -> None:
        """Validate runtime environment."""
        try:
            # Basic environment validation
            if not skip_venv:
                import os
                venv_path = os.environ.get('VIRTUAL_ENV')
                if not venv_path:
                    raise Exception("Not running in a virtual environment")
            
            # Basic Python version check
            import sys
            if sys.version_info < (3, 10):
                raise Exception("Python 3.10+ required")
            
            logger.debug("Environment validation passed")
            
        except Exception as e:
            console.print(f"[red]Environment error: {e}[/red]")
            
            if "virtual environment" in str(e):
                console.print("[yellow]Run: source .venv/bin/activate[/yellow]")
            elif "Python" in str(e):
                console.print("[yellow]Ensure Python 3.10+ is installed[/yellow]")
            
            raise click.ClickException(str(e))
    
    def handle_error(self, error: Exception) -> None:
        """Handle and display errors appropriately."""
        if isinstance(error, EhAyeError):
            console.print(f"[red]Error: {error.message}[/red]")
            if error.code:
                console.print(f"[dim]Error code: {error.code}[/dim]")
        else:
            console.print(f"[red]Unexpected error: {error}[/red]")
            logger.error(f"Unexpected error in {self.app_name}: {error}", exc_info=True)
        
        raise click.ClickException(str(error))
    
    def add_common_options(self, callback):
        """Decorator to add common CLI options."""
        callback = click.option(
            "--verbose", "-v", is_flag=True,
            help="Enable verbose logging"
        )(callback)
        
        callback = click.option(
            "--quiet", "-q", is_flag=True,
            help="Suppress output except errors"
        )(callback)
        
        callback = click.option(
            "--config", "-c", type=click.Path(exists=True),
            help="Custom configuration file path"
        )(callback)
        
        return callback


def common_setup(
    ctx: click.Context = None,
    verbose: bool = False,
    quiet: bool = False,
    config: Optional[Path] = None,
    skip_venv: bool = False
) -> BaseCLI:
    """Common setup for all CLI commands."""
    # Get CLI instance from context
    cli = "ehaye" if ctx is None else getattr(ctx, 'info_name', 'ehaye')
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
    import sys
    sys.exit(130)  # Standard exit code for SIGINT (128 + 2)


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    return click.confirm(message, default=default)


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