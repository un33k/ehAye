"""Benchmark CLI interface."""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from ..benchmarks.reports import print_benchmark_report, print_comparison_report, export_results_to_json
from ..benchmarks.runner import benchmark_model, compare_models
from ..benchmarks.system import validate_benchmark_environment
from ..core.logging import get_logger
from ..models.registry import get_installed_models, search_models
from .base import BaseCLI, common_setup, handle_keyboard_interrupt, show_error, show_info, show_success

app = typer.Typer(name="benchmark", help="Performance benchmarking for LLM models")
console = Console()
logger = get_logger("cli.benchmark")


@app.command()
def single(
    ctx: typer.Context,
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to benchmark"),
    tokens: int = typer.Option(100, "--tokens", "-t", help="Tokens to generate per run"),
    runs: int = typer.Option(3, "--runs", "-r", help="Number of benchmark runs"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
):
    """Benchmark a single model."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Validate environment
        if not validate_benchmark_environment():
            show_error("Environment validation failed")
            return
        
        # Select model if not provided
        if not model:
            model = select_model_interactive()
            if not model:
                return
        
        show_info(f"Benchmarking {model} with {runs} runs of {tokens} tokens each")
        
        # Run benchmark
        result = benchmark_model(model, tokens, runs)
        
        # Display results
        print_benchmark_report(result)
        
        # Save results if requested
        if output:
            if export_results_to_json([result], str(output)):
                show_success(f"Results saved to {output}")
            else:
                show_error(f"Failed to save results to {output}")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
def compare(
    ctx: typer.Context,
    models: Optional[List[str]] = typer.Option(None, "--models", "-m", help="Models to compare"),
    tokens: int = typer.Option(100, "--tokens", "-t", help="Tokens to generate per run"),
    runs: int = typer.Option(2, "--runs", "-r", help="Number of benchmark runs"),
    all_models: bool = typer.Option(False, "--all", "-a", help="Compare all installed models"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
):
    """Compare multiple models."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Validate environment
        if not validate_benchmark_environment():
            show_error("Environment validation failed")
            return
        
        # Get models to compare
        if all_models:
            installed_models = get_installed_models()
            model_ids = [m.id for m in installed_models]
        elif models:
            model_ids = list(models)
        else:
            model_ids = select_models_interactive()
            if not model_ids:
                return
        
        if len(model_ids) < 2:
            show_error("Need at least 2 models to compare")
            return
        
        show_info(f"Comparing {len(model_ids)} models with {runs} runs of {tokens} tokens each")
        
        # Run comparison
        results = compare_models(model_ids, tokens, runs)
        
        # Display results
        if results:
            print_comparison_report(results)
            
            # Save results if requested
            if output:
                if export_results_to_json(results, str(output)):
                    show_success(f"Results saved to {output}")
                else:
                    show_error(f"Failed to save results to {output}")
        else:
            show_error("No successful benchmarks completed")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
def list_models(
    ctx: typer.Context,
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Search models"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
):
    """List available models for benchmarking."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        if search:
            models = search_models(query=search)
        else:
            models = get_installed_models()
        
        if not models:
            show_error("No models found")
            return
        
        console.print("📊 Available Models for Benchmarking:")
        console.print("=" * 50)
        
        for i, model in enumerate(models, 1):
            console.print(f"  {i:2d}. {model.display_name}")
            if verbose:
                console.print(f"      ID: {model.id}")
                console.print(f"      Category: {model.category}")
                if model.size_gb:
                    console.print(f"      Est. Size: {model.size_gb:.1f}GB")
        
        console.print(f"\n💡 Use: ehaye-benchmark single --model <model_id>")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
def validate(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Config file"),
):
    """Validate benchmark environment."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        console.print("🔬 Validating Benchmark Environment...")
        console.print("=" * 40)
        
        if validate_benchmark_environment():
            show_success("Environment validation passed")
            console.print("✅ Ready for benchmarking")
        else:
            show_error("Environment validation failed")
            console.print("❌ Please fix issues before benchmarking")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


def select_model_interactive() -> Optional[str]:
    """Interactive model selection."""
    models = get_installed_models()
    
    if not models:
        show_error("No models found. Install models first using: ehaye-models download")
        return None
    
    console.print("📊 Available Models for Benchmarking:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        console.print(f"  {i:2d}. {model.display_name}")
    
    try:
        choice = typer.prompt("\nSelect model number", type=int)
        
        if 1 <= choice <= len(models):
            selected = models[choice - 1]
            show_info(f"Selected: {selected.display_name}")
            return selected.id
        else:
            show_error("Invalid selection")
            return None
            
    except (ValueError, typer.Abort):
        return None


def select_models_interactive() -> List[str]:
    """Interactive multiple model selection."""
    models = get_installed_models()
    
    if not models:
        show_error("No models found. Install models first using: ehaye-models download")
        return []
    
    console.print("📊 Available Models for Comparison:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        console.print(f"  {i:2d}. {model.display_name}")
    
    console.print(f"  {len(models)+1:2d}. All models")
    
    try:
        choices_str = typer.prompt(
            "\nSelect model numbers (comma-separated, ranges like 1-3, or 'all')",
            type=str
        )
        
        if choices_str.lower() == 'all' or choices_str == str(len(models)+1):
            return [m.id for m in models]
        
        # Parse selections
        selected_ids = []
        parts = [p.strip() for p in choices_str.split(',')]
        
        for part in parts:
            if '-' in part:
                # Range
                start, end = map(int, part.split('-'))
                for i in range(start, end + 1):
                    if 1 <= i <= len(models):
                        selected_ids.append(models[i-1].id)
            else:
                # Single number
                i = int(part)
                if 1 <= i <= len(models):
                    selected_ids.append(models[i-1].id)
        
        if selected_ids:
            show_info(f"Selected {len(selected_ids)} models for comparison")
            return selected_ids
        else:
            show_error("No valid selections")
            return []
            
    except (ValueError, typer.Abort):
        return []


def main():
    """Main entry point for benchmark CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()