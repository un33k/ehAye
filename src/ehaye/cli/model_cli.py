"""Model management CLI interface with flag-based commands."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

console = Console()


def setup_logging(verbose: bool, debug: bool):
    """Configure logging based on verbosity flags."""
    import logging
    from ..core.logging import ehaye_logger
    
    if debug:
        # Show all logs including DEBUG level
        level = "DEBUG"
    elif verbose:
        # Show INFO level and above
        level = "INFO"
    else:
        # No logs by default (only CRITICAL)
        level = "CRITICAL"
    
    # Configure the global logger
    ehaye_logger.setup(level=level, enable_rich=True)


def show_help():
    """Show help message."""
    console.print("ehAye Models CLI - manage your local LLM models")
    console.print("\nUsage:")
    console.print("  ehaye-models [ACTION] [OPTIONS]")
    console.print("\nAction Flags (choose one):")
    console.print("  -l, --list       List installed models")
    console.print("  -s, --search     Search available models")
    console.print("  -d, --download   Download a model")
    console.print("  -r, --remove     Remove a model")
    console.print("  -i, --info       Show model information")
    console.print("\nParameters:")
    console.print("  -q, --query      Search query")
    console.print("  -f, --flavor     Model flavor/size (e.g., 7B, mini)")
    console.print("  -m, --model      Model ID to operate on")
    console.print("  -p, --provider   Provider to use (ollama/mlx) [default: ollama]")
    console.print("  -c, --category   Filter by category")
    console.print("\nOptions:")
    console.print("  -v, --verbose    Verbose output (INFO level logs)")
    console.print("  --debug          Debug output (all logs)")
    console.print("  --interactive    Interactive selection")
    console.print("  --force          Force operation")
    console.print("\nExamples:")
    console.print("  ehaye-models -s -q deepseek -f 7B -p ollama")
    console.print("  ehaye-models -s -f 1B")
    console.print("  ehaye-models -l")
    console.print("  ehaye-models -d -m phi3")
    console.print("  ehaye-models -s -p mlx")
    console.print("  ehaye-models -l -p mlx")


def main():
    """Main entry point for model CLI."""
    try:
        import sys
        args = sys.argv[1:]  # Get command line arguments
        
        # Quick scan for verbosity flags to set up logging early
        verbose = any(arg in ['-v', '--verbose'] for arg in args)
        debug = any(arg == '--debug' for arg in args)
        
        # Setup logging immediately before any other operations
        setup_logging(verbose, debug)
        
        # Parse arguments manually for better control
        actions = []
        params = {}
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in ['-l', '--list']:
                actions.append('list')
            elif arg in ['-s', '--search']:
                actions.append('search')
            elif arg in ['-d', '--download']:
                actions.append('download')
            elif arg in ['-r', '--remove']:
                actions.append('remove')
            elif arg in ['-i', '--info']:
                actions.append('info')
            elif arg in ['-q', '--query']:
                if i + 1 < len(args):
                    params['query'] = args[i + 1]
                    i += 1
            elif arg in ['-f', '--flavor']:
                if i + 1 < len(args):
                    params['flavor'] = args[i + 1]
                    i += 1
            elif arg in ['-m', '--model']:
                if i + 1 < len(args):
                    params['model'] = args[i + 1]
                    i += 1
            elif arg in ['-p', '--provider']:
                if i + 1 < len(args):
                    params['provider'] = args[i + 1]
                    i += 1
            elif arg in ['-c', '--category']:
                if i + 1 < len(args):
                    params['category'] = args[i + 1]
                    i += 1
            elif arg in ['-v', '--verbose']:
                params['verbose'] = True
            elif arg == '--debug':
                params['debug'] = True
            elif arg == '--interactive':
                params['interactive'] = True
            elif arg == '--force':
                params['force'] = True
            elif arg in ['-h', '--help']:
                show_help()
                return
            
            i += 1
        
        # Set defaults
        params.setdefault('verbose', verbose)
        params.setdefault('debug', debug)
        params.setdefault('interactive', False)
        params.setdefault('force', False)
        
        # Import after logging setup to avoid early log messages
        from ..core.logging import get_logger
        from ..backends.manager import get_backend_manager
        from .base import common_setup, confirm_action, handle_keyboard_interrupt, show_error, show_info, show_success
        
        # Check action count
        if len(actions) == 0:
            show_help()
            return
        elif len(actions) > 1:
            show_error("Please specify only one action flag")
            return
        
        logger = get_logger("cli.models")
        
        # Setup context
        try:
            common_setup(None, params.get('verbose', False), False, None, skip_venv=True)
        except:
            pass  # Skip setup issues for now
        
        # Get backend manager
        manager = get_backend_manager()
        provider = params.get('provider', 'ollama')  # Default to ollama
        backend_obj = manager.get_backend(provider)
        
        # Execute action
        action = actions[0]
        if action == 'list':
            handle_list(backend_obj, manager, params)
        elif action == 'search':
            handle_search(backend_obj, manager, params)
        elif action == 'download':
            handle_download(backend_obj, params)
        elif action == 'remove':
            handle_remove(backend_obj, params)
        elif action == 'info':
            handle_info(backend_obj, params)
            
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        logger.error(f"Command failed: {e}")
        show_error(f"Command failed: {e}")


def handle_list(backend_obj, manager, params):
    """Handle list operation."""
    try:
        from ..core.logging import get_logger
        from .base import show_error, show_info, show_success, confirm_action
        logger = get_logger("cli.models")
        provider = params.get('provider', 'ollama')
        query = params.get('query')
        category = params.get('category')
        flavor = params.get('flavor')
        verbose = params.get('verbose', False)
        
        if provider != 'all':
            models = backend_obj.list_models()
            console.print(f"📦 Installed Models ({provider}):")
        else:
            all_models = manager.list_all_models()
            models = []
            for provider_name, provider_models in all_models.items():
                for model in provider_models:
                    model.description = f"[{provider_name}] " + (model.description or "")
                    models.append(model)
            console.print("📦 Installed Models (All Providers):")
        
        # Apply filters
        if query:
            query_lower = query.lower()
            models = [m for m in models if query_lower in m.name.lower() or query_lower in m.id.lower()]
        
        if category:
            models = [m for m in models if m.family and category.lower() in m.family.lower()]
        
        if flavor:
            flavor_lower = flavor.lower()
            models = [m for m in models if m.size and flavor_lower in m.size.lower()]
        
        if not models:
            show_error("No models found")
            return
        
        console.print("=" * 60)
        
        for i, model in enumerate(models, 1):
            size_info = f" ({model.size})" if model.size else ""
            console.print(f"  {i:2d}. {model.name}{size_info}")
            
            if verbose:
                console.print(f"      ID: {model.id}")
                if '[' in (model.description or ''):
                    provider_name = model.description.split(']')[0][1:]
                    console.print(f"      Provider: {provider_name}")
                if model.family:
                    console.print(f"      Family: {model.family}")
        
        console.print(f"\n💡 Total: {len(models)} model(s) installed")
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        show_error(f"Failed to list models: {e}")


def handle_search(backend_obj, manager, params):
    """Handle search operation."""
    try:
        from ..core.logging import get_logger
        from .base import show_error, show_info, show_success, confirm_action
        logger = get_logger("cli.models")
        provider = params.get('provider', 'ollama')
        query = params.get('query')
        flavor = params.get('flavor')
        verbose = params.get('verbose', False)
        
        if provider != 'all':
            models = backend_obj.search_models(query)
            console.print(f"🔍 Available Models for Download ({provider}):")
        else:
            all_models = manager.search_all_models(query)
            models = []
            for provider_name, provider_models in all_models.items():
                for model in provider_models:
                    model.description = f"[{provider_name}] " + (model.description or "")
                    models.append(model)
            console.print("🔍 Available Models for Download (All Providers):")
        
        # Apply flavor filter
        if flavor:
            flavor_lower = flavor.lower()
            models = [m for m in models if m.size and flavor_lower in m.size.lower() or 
                     flavor_lower in m.id.lower() or flavor_lower in m.name.lower()]
        
        if not models:
            show_error("No models found")
            return
        
        console.print("=" * 60)
        
        for i, model in enumerate(models, 1):
            size_info = f" ({model.size})" if model.size else ""
            console.print(f"  {i:2d}. {model.name}{size_info} [-m {model.id}]")
            
            if verbose:
                if '[' in (model.description or ''):
                    provider_name = model.description.split(']')[0][1:]
                    console.print(f"      Provider: {provider_name}")
                if model.family:
                    console.print(f"      Family: {model.family}")
        
        console.print(f"\n💡 Use: ehaye-models -d -m <model_id> -p <provider>")
        console.print(f"💡 Use: ehaye-models -d --interactive")
        
    except Exception as e:
        logger.error(f"Failed to search models: {e}")
        show_error(f"Failed to search models: {e}")


def handle_download(backend_obj, params):
    """Handle download operation."""
    try:
        from ..core.logging import get_logger
        from .base import show_error, show_info, show_success, confirm_action
        logger = get_logger("cli.models")
        model_id = params.get('model')
        interactive = params.get('interactive', False)
        force = params.get('force', False)
        verbose = params.get('verbose', False)
        
        if interactive or not model_id:
            model_id = select_model_for_download(backend_obj)
            if not model_id:
                return
        
        if not model_id:
            show_error("Please specify a model ID with -m/--model or use --interactive")
            return
        
        # Check if already installed
        if not force:
            installed = backend_obj.list_models()
            if any(m.id == model_id for m in installed):
                show_info(f"Model {model_id} already installed")
                if not confirm_action("Download anyway?"):
                    return
        
        show_info(f"Downloading {model_id}...")
        
        # Progress callback
        def progress_callback(message: str):
            if verbose:
                console.print(f"  {message}")
        
        # Download model
        model_info = backend_obj.download_model(model_id, progress_callback if verbose else None)
        
        show_success(f"Successfully downloaded {model_info.name}")
        console.print(f"  Model ID: {model_info.id}")
        if model_info.size:
            console.print(f"  Size: {model_info.size}")
            
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        show_error(f"Failed to download model: {e}")


def handle_remove(backend_obj, params):
    """Handle remove operation."""
    try:
        from ..core.logging import get_logger
        from .base import show_error, show_info, show_success, confirm_action
        logger = get_logger("cli.models")
        model_id = params.get('model')
        interactive = params.get('interactive', False)
        force = params.get('force', False)
        
        if interactive or not model_id:
            model_id = select_installed_model(backend_obj)
            if not model_id:
                return
        
        if not model_id:
            show_error("Please specify a model ID with -m/--model or use --interactive")
            return
        
        # Confirm removal
        if not force:
            if not confirm_action(f"Remove model {model_id}?"):
                return
        
        show_info(f"Removing {model_id}...")
        
        # Remove model
        if backend_obj.remove_model(model_id):
            show_success(f"Successfully removed {model_id}")
        else:
            show_error(f"Failed to remove {model_id}")
            
    except Exception as e:
        logger.error(f"Failed to remove model: {e}")
        show_error(f"Failed to remove model: {e}")


def handle_info(backend_obj, params):
    """Handle info operation."""
    try:
        from ..core.logging import get_logger
        from .base import show_error, show_info, show_success, confirm_action
        logger = get_logger("cli.models")
        model_id = params.get('model')
        interactive = params.get('interactive', False)
        
        if interactive or not model_id:
            model_id = select_installed_model(backend_obj)
            if not model_id:
                return
        
        if not model_id:
            show_error("Please specify a model ID with -m/--model or use --interactive")
            return
        
        # Get model info
        model_info = backend_obj.get_model_info(model_id)
        
        if not model_info:
            show_error(f"Model {model_id} not found")
            return
        
        # Display info
        console.print(f"\n📋 Model Information: {model_info.name}")
        console.print("=" * 60)
        
        from rich.table import Table
        table = Table(show_header=False)
        table.add_column("Property", style="bold blue")
        table.add_column("Value")
        
        table.add_row("Model ID", model_info.id)
        table.add_row("Name", model_info.name)
        
        if model_info.family:
            table.add_row("Family", model_info.family)
        
        if model_info.size:
            table.add_row("Size", model_info.size)
        
        if model_info.format:
            table.add_row("Format", model_info.format)
        
        if model_info.description:
            table.add_row("Description", model_info.description)
        
        console.print(table)
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        show_error(f"Failed to get model info: {e}")


def select_model_for_download(backend_obj) -> Optional[str]:
    """Interactive model selection for download."""
    from .base import show_error
    available = backend_obj.search_models()
    
    if not available:
        show_error("No models available for download")
        return None
    
    console.print("🔍 Available Models for Download:")
    console.print("=" * 50)
    
    for i, model in enumerate(available, 1):
        size_info = f" ({model.size})" if model.size else ""
        console.print(f"  {i:2d}. {model.name}{size_info}")
    
    while True:
        try:
            choice_str = typer.prompt("\nSelect model number (or 'q' to quit)")
            
            # Handle quit conditions
            if choice_str.lower().strip() in ['q', 'quit']:
                console.print("👋 Cancelled")
                return None
                
            try:
                choice = int(choice_str)
            except ValueError:
                show_error("Please enter a valid number or 'q' to quit")
                continue
            
            if 1 <= choice <= len(available):
                return available[choice - 1].id
            else:
                show_error("Invalid selection")
                continue
                
        except typer.Abort:
            console.print("👋 Cancelled")
            return None


def select_installed_model(backend_obj) -> Optional[str]:
    """Interactive selection of installed model."""
    from .base import show_error
    models = backend_obj.list_models()
    
    if not models:
        show_error("No models installed")
        return None
    
    console.print("📦 Installed Models:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        size_info = f" ({model.size})" if model.size else ""
        console.print(f"  {i:2d}. {model.name}{size_info}")
    
    while True:
        try:
            choice_str = typer.prompt("\nSelect model number (or 'q' to quit)")
            
            # Handle quit conditions
            if choice_str.lower().strip() in ['q', 'quit']:
                console.print("👋 Cancelled")
                return None
                
            try:
                choice = int(choice_str)
            except ValueError:
                show_error("Please enter a valid number or 'q' to quit")
                continue
            
            if 1 <= choice <= len(models):
                return models[choice - 1].id
            else:
                show_error("Invalid selection")
                continue
                
        except typer.Abort:
            console.print("👋 Cancelled")
            return None


if __name__ == "__main__":
    main()