"""Model management CLI interface."""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.logging import get_logger
from ..models.categories import group_models
from ..models.manager import download_model, list_available_models, remove_model, search_available_models
from ..models.registry import get_installed_models, search_models
from .base import BaseCLI, common_setup, confirm_action, handle_keyboard_interrupt, show_error, show_info, show_success

app = typer.Typer(name="models", help="Model management and installation")
console = Console()
logger = get_logger("cli.models")


@app.command()
def list(
    ctx: typer.Context,
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search models"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """List installed models."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        # Get models
        if search:
            models = search_models(query=search, category=category)
        else:
            models = get_installed_models()
            if category:
                models = [m for m in models if m.category == category]
        
        if not models:
            show_error("No models found")
            return
        
        # Group by category
        grouped = group_models([m.id for m in models])
        
        console.print("📦 Installed Models:")
        console.print("=" * 60)
        
        total_models = 0
        for category_name, category_models in grouped.items():
            if not category_models:
                continue
            
            # Category header
            emoji = category_models[0].emoji
            console.print(f"\n{emoji} {category_name.title()} Models:")
            
            for model in category_models:
                size_info = f" ({model.size_params})" if model.size_params else ""
                console.print(f"  • {model.name}{size_info}")
                
                if verbose:
                    console.print(f"    ID: {model.id}")
                    if model.size_gb:
                        console.print(f"    Size: ~{model.size_gb:.1f}GB")
            
            total_models += len(category_models)
        
        console.print(f"\n💡 Total: {total_models} model(s) installed")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command("search", short_help="Search models")
def search(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Search query"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """Search available models for download."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        # Get available models
        if query:
            models = search_available_models(query)
        else:
            models = list_available_models()
        
        if not models:
            show_error("No models found")
            return
        
        console.print("🔍 Available Models for Download:")
        console.print("=" * 60)
        
        for i, model_id in enumerate(models, 1):
            # Categorize model for display
            from ..models.categories import categorize_model
            model_info = categorize_model(model_id)
            
            console.print(f"  {i:2d}. {model_info.display_name}")
            
            if verbose:
                console.print(f"      ID: {model_id}")
                console.print(f"      Category: {model_info.category}")
                if model_info.size_gb:
                    console.print(f"      Est. Size: {model_info.size_gb:.1f}GB")
        
        console.print(f"\n💡 Use: ehaye-models download <model_id>")
        console.print(f"💡 Use: ehaye-models download --interactive")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command("download", short_help="Download models")
def download(
    ctx: typer.Context,
    model_id: Optional[str] = typer.Argument(None, help="Model ID to download"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive selection"),
    force: bool = typer.Option(False, "--force", "-f", help="Force download if exists"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """Download and install a model."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Interactive selection if no model provided
        if interactive or not model_id:
            model_id = select_model_for_download()
            if not model_id:
                return
        
        # Check if already installed
        if not force:
            installed = get_installed_models()
            if any(m.id == model_id for m in installed):
                show_info(f"Model {model_id} already installed")
                if not confirm_action("Download anyway?"):
                    return
        
        show_info(f"Downloading {model_id}...")
        
        # Download model
        model_info = download_model(model_id)
        
        show_success(f"Successfully downloaded {model_info.display_name}")
        console.print(f"  Category: {model_info.category}")
        console.print(f"  Model ID: {model_info.id}")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
def remove(
    ctx: typer.Context,
    model_id: Optional[str] = typer.Argument(None, help="Model ID to remove"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive selection"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """Remove an installed model."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Interactive selection if no model provided
        if interactive or not model_id:
            model_id = select_installed_model()
            if not model_id:
                return
        
        # Confirm removal
        if not force:
            if not confirm_action(f"Remove model {model_id}?"):
                return
        
        show_info(f"Removing {model_id}...")
        
        # Remove model
        if remove_model(model_id):
            show_success(f"Successfully removed {model_id}")
        else:
            show_error(f"Failed to remove {model_id}")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
def info(
    ctx: typer.Context,
    model_id: Optional[str] = typer.Argument(None, help="Model ID to show info for"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive selection"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """Show detailed model information."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        # Interactive selection if no model provided
        if interactive or not model_id:
            model_id = select_installed_model()
            if not model_id:
                return
        
        # Find model
        models = get_installed_models()
        model_info = next((m for m in models if m.id == model_id), None)
        
        if not model_info:
            show_error(f"Model {model_id} not found")
            return
        
        # Display info
        console.print(f"\n📋 Model Information: {model_info.display_name}")
        console.print("=" * 60)
        
        table = Table(show_header=False)
        table.add_column("Property", style="bold blue")
        table.add_column("Value")
        
        table.add_row("Model ID", model_info.id)
        table.add_row("Name", model_info.name)
        table.add_row("Category", f"{model_info.emoji} {model_info.category}")
        
        if model_info.size_params:
            table.add_row("Parameters", model_info.size_params)
        
        if model_info.size_gb:
            table.add_row("Est. Size", f"{model_info.size_gb:.1f}GB")
        
        if model_info.quantization:
            table.add_row("Quantization", model_info.quantization)
        
        console.print(table)
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


def select_model_for_download() -> Optional[str]:
    """Interactive model selection for download."""
    available = list_available_models()
    
    if not available:
        show_error("No models available for download")
        return None
    
    console.print("🔍 Available Models for Download:")
    console.print("=" * 50)
    
    for i, model_id in enumerate(available, 1):
        from ..models.categories import categorize_model
        model_info = categorize_model(model_id)
        console.print(f"  {i:2d}. {model_info.display_name}")
    
    try:
        choice = typer.prompt("\nSelect model number", type=int)
        
        if 1 <= choice <= len(available):
            return available[choice - 1]
        else:
            show_error("Invalid selection")
            return None
            
    except (ValueError, typer.Abort):
        return None


def select_installed_model() -> Optional[str]:
    """Interactive selection of installed model."""
    models = get_installed_models()
    
    if not models:
        show_error("No models installed")
        return None
    
    console.print("📦 Installed Models:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        console.print(f"  {i:2d}. {model.display_name}")
    
    try:
        choice = typer.prompt("\nSelect model number", type=int)
        
        if 1 <= choice <= len(models):
            return models[choice - 1].id
        else:
            show_error("Invalid selection")
            return None
            
    except (ValueError, typer.Abort):
        return None


# Register command aliases
app.command("s", help="Search available models (alias for search)")(search)
app.command("d", help="Download models (alias for download)")(download)
app.command("l", help="List installed models (alias for list)")(list)
app.command("r", help="Remove models (alias for remove)")(remove)
app.command("i", help="Show model info (alias for info)")(info)


def main():
    """Main entry point for model CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()