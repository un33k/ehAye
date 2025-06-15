"""Model management CLI interface."""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.logging import get_logger
from ..backends.manager import get_backend_manager, get_backend
from .base import BaseCLI, common_setup, confirm_action, handle_keyboard_interrupt, show_error, show_info, show_success

app = typer.Typer(name="models", help="Model management and installation")
console = Console()
logger = get_logger("cli.models")


@app.command()
def list(
    ctx: typer.Context,
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search models"),
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="Backend to use (ollama/mlx)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """List installed models."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        # Get backend manager
        manager = get_backend_manager()
        
        if backend:
            # List models from specific backend
            if not manager.is_backend_available(backend):
                show_error(f"Backend '{backend}' not available")
                available = manager.list_backends()
                if available:
                    show_info(f"Available backends: {', '.join(available)}")
                return
            
            backend_obj = manager.get_backend(backend)
            models = backend_obj.list_models()
            
            if search:
                query_lower = search.lower()
                models = [m for m in models if query_lower in m.name.lower() or query_lower in m.id.lower()]
            
            if category:
                models = [m for m in models if m.family and category.lower() in m.family.lower()]
        else:
            # List models from all backends
            all_models = manager.list_all_models()
            models = []
            for backend_name, backend_models in all_models.items():
                for model in backend_models:
                    model.description = f"[{backend_name}] " + (model.description or "")
                    models.append(model)
            
            if search:
                query_lower = search.lower()
                models = [m for m in models if query_lower in m.name.lower() or query_lower in m.id.lower()]
            
            if category:
                models = [m for m in models if m.family and category.lower() in m.family.lower()]
        
        if not models:
            show_error("No models found")
            return
        
        console.print("📦 Installed Models:")
        console.print("=" * 60)
        
        for i, model in enumerate(models, 1):
            size_info = f" ({model.size})" if model.size else ""
            console.print(f"  {i:2d}. {model.name}{size_info}")
            
            if verbose:
                console.print(f"      ID: {model.id}")
                console.print(f"      Backend: {model.description.split(']')[0][1:] if '[' in model.description else 'unknown'}")
                if model.family:
                    console.print(f"      Family: {model.family}")
        
        console.print(f"\n💡 Total: {len(models)} model(s) installed")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command("search", short_help="Search models")
def search(
    ctx: typer.Context,
    query: Optional[str] = typer.Argument(None, help="Search query"),
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="Backend to use (ollama/mlx)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """Search available models for download."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        # Get backend manager
        manager = get_backend_manager()
        
        if backend:
            # Search models from specific backend
            if not manager.is_backend_available(backend):
                show_error(f"Backend '{backend}' not available")
                available = manager.list_backends()
                if available:
                    show_info(f"Available backends: {', '.join(available)}")
                return
            
            backend_obj = manager.get_backend(backend)
            models = backend_obj.search_models(query)
            
            console.print(f"🔍 Available Models for Download ({backend}):")
        else:
            # Search models from all backends
            all_models = manager.search_all_models(query)
            models = []
            for backend_name, backend_models in all_models.items():
                for model in backend_models:
                    model.description = f"[{backend_name}] " + (model.description or "")
                    models.append(model)
            
            console.print("🔍 Available Models for Download (All Backends):")
        
        if not models:
            show_error("No models found")
            return
        
        console.print("=" * 60)
        
        for i, model in enumerate(models, 1):
            size_info = f" ({model.size})" if model.size else ""
            console.print(f"  {i:2d}. {model.name}{size_info}")
            
            if verbose:
                console.print(f"      ID: {model.id}")
                backend_name = model.description.split(']')[0][1:] if '[' in model.description else 'unknown'
                console.print(f"      Backend: {backend_name}")
                if model.family:
                    console.print(f"      Family: {model.family}")
        
        console.print(f"\n💡 Use: ali download <model_id> --backend <backend>")
        console.print(f"💡 Use: ali download --interactive")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command("download", short_help="Download models")
def download(
    ctx: typer.Context,
    model_id: Optional[str] = typer.Argument(None, help="Model ID to download"),
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="Backend to use (ollama/mlx)"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive selection"),
    force: bool = typer.Option(False, "--force", "-f", help="Force download if exists"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file"),
):
    """Download and install a model."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Get backend
        manager = get_backend_manager()
        backend_obj = manager.get_backend(backend)
        
        # Interactive selection if no model provided
        if interactive or not model_id:
            model_id = select_model_for_download(backend_obj)
            if not model_id:
                return
        
        # Check if already installed
        if not force:
            installed = backend_obj.list_models()
            if any(m.id == model_id for m in installed):
                show_info(f"Model {model_id} already installed")
                if not confirm_action("Download anyway?"):
                    return
        
        show_info(f"Downloading {model_id} using {backend or 'default'} backend...")
        
        # Progress callback
        def progress_callback(message: str):
            if verbose:
                console.print(f"  {message}")
        
        # Download model
        model_info = backend_obj.download_model(model_id, progress_callback if verbose else None)
        
        show_success(f"Successfully downloaded {model_info.name}")
        console.print(f"  Backend: {backend or 'default'}")
        console.print(f"  Model ID: {model_info.id}")
        if model_info.size:
            console.print(f"  Size: {model_info.size}")
        
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


def select_model_for_download(backend_obj) -> Optional[str]:
    """Interactive model selection for download."""
    available = backend_obj.search_models()
    
    if not available:
        show_error("No models available for download")
        return None
    
    console.print("🔍 Available Models for Download:")
    console.print("=" * 50)
    
    for i, model in enumerate(available, 1):
        size_info = f" ({model.size})" if model.size else ""
        console.print(f"  {i:2d}. {model.name}{size_info}")
    
    try:
        choice = typer.prompt("\nSelect model number", type=int)
        
        if 1 <= choice <= len(available):
            return available[choice - 1].id
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