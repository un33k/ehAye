"""Benchmark CLI interface."""

import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console

# Import actual benchmarking modules
from ..benchmarking import (
    print_benchmark_report, 
    print_comparison_report, 
    export_results_to_json,
    benchmark_model, 
    compare_models,
    validate_benchmark_environment,
)
from ..logging.logger import get_logger
from ..models.registry import get_installed_models, search_models
from .base import BaseCLI, common_setup, handle_keyboard_interrupt, show_error, show_info, show_success

@click.group(name="benchmark")
def app():
    """Performance benchmarking for LLM models"""
    pass
console = Console()
logger = get_logger("cli.benchmark")


@app.command()
@click.option("--model", "-m", help="Model to benchmark")
@click.option("--tokens", "-t", default=100, help="Tokens to generate per run")
@click.option("--runs", "-r", default=3, help="Number of benchmark runs")
@click.option("--output", "-o", type=click.Path(), help="Save results to JSON file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def single(ctx, model, tokens, runs, output, verbose, quiet, config):
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
@click.option("--models", "-m", multiple=True, help="Models to compare")
@click.option("--tokens", "-t", default=100, help="Tokens to generate per run")
@click.option("--runs", "-r", default=2, help="Number of benchmark runs")
@click.option("--all", "-a", is_flag=True, help="Compare all installed models")
@click.option("--output", "-o", type=click.Path(), help="Save results to JSON file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def compare(ctx, models, tokens, runs, all, output, verbose, quiet, config):
    """Compare multiple models."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        # Validate environment
        if not validate_benchmark_environment():
            show_error("Environment validation failed")
            return
        
        # Get models to compare
        if all:
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
@click.option("--search", "-s", help="Search models")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def list_models(ctx, search, verbose, quiet, config):
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
        
        console.print(f"\n💡 Use: ali perf single --model <model_id>")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file")
@click.pass_context
def validate(ctx, verbose, quiet, config):
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
        show_error("No models found. Install models first using: ali download")
        return None
    
    console.print("📊 Available Models for Benchmarking:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        console.print(f"  {i:2d}. {model.display_name}")
    
    try:
        choice = click.prompt("\nSelect model number", type=int)
        
        if 1 <= choice <= len(models):
            selected = models[choice - 1]
            show_info(f"Selected: {selected.display_name}")
            return selected.id
        else:
            show_error("Invalid selection")
            return None
            
    except (ValueError, click.Abort):
        return None


def select_models_interactive() -> List[str]:
    """Interactive multiple model selection."""
    models = get_installed_models()
    
    if not models:
        show_error("No models found. Install models first using: ali download")
        return []
    
    console.print("📊 Available Models for Comparison:")
    console.print("=" * 50)
    
    for i, model in enumerate(models, 1):
        console.print(f"  {i:2d}. {model.display_name}")
    
    console.print(f"  {len(models)+1:2d}. All models")
    
    try:
        choices_str = click.prompt(
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
            
    except (ValueError, click.Abort):
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