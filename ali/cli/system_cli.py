"""System management CLI interface."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Placeholder imports
# from ..benchmarking.utils import get_system_info, validate_benchmark_environment

def get_system_info():
    """Placeholder system info function."""
    return {
        "memory": {"total_gb": 16.0, "available_gb": 8.0, "used_percent": 50.0, "process_mb": 100.0},
        "cpu": {"brand": "Apple M1", "count": 8, "count_logical": 8, "usage_percent": 25.0},
        "gpu": {"available": True, "memory_mb": 7168, "memory_gb": 7.0, "cores": 8},
        "thermal_state": "nominal"
    }

def validate_benchmark_environment():
    """Placeholder benchmark validation."""
    return True
from ..configuration import get_config
from ..logging.logger import get_logger
from .base import BaseCLI, common_setup, handle_keyboard_interrupt, show_error, show_info, show_success

@click.group(name="system")
def app():
    """System management and diagnostics"""
    pass
console = Console()
logger = get_logger("cli.system")


@app.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.pass_context
def info(ctx, verbose, quiet, config):
    """Show system information."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        console.print("🖥️  System Information")
        console.print()
        
        # Get comprehensive system info
        system_info = get_system_info()
        
        # Memory information
        memory_info = system_info.get("memory", {})
        console.print(Panel(
            f"Total:     {memory_info.get('total_gb', 0):.1f}GB\n"
            f"Available: {memory_info.get('available_gb', 0):.1f}GB\n"
            f"Used:      {memory_info.get('used_percent', 0):.1f}%\n"
            f"Process:   {memory_info.get('process_mb', 0):.1f}MB",
            title="💾 MEM",
            border_style="blue"
        ))
        
        # CPU information
        cpu_info = system_info.get("cpu", {})
        console.print(Panel(
            f"Brand: {cpu_info.get('brand', 'Unknown')}\n"
            f"Cores: {cpu_info.get('count', 0)} physical, {cpu_info.get('count_logical', 0)} logical\n"
            f"Usage: {cpu_info.get('usage_percent', 0):.1f}%",
            title="🧠 CPU",
            border_style="green"
        ))
        
        # GPU information
        gpu_info = system_info.get("gpu", {})
        if gpu_info.get("available"):
            gpu_details = []
            
            # Memory info (clarify it's pre-allocated)
            if gpu_info.get('memory_mb'):
                gpu_details.append(f"Memory: {gpu_info.get('memory_mb', 0)}MB ({gpu_info.get('memory_gb', 0):.1f}GB) (iogpu allocated)")
            
            # Core count
            if gpu_info.get('cores'):
                gpu_details.append(f"Cores:  {gpu_info.get('cores')}")
            
            # Status
            gpu_details.append("Status: Available")
            
            console.print(Panel(
                "\n".join(gpu_details),
                title="🎮 GPU",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                "Status: Not detected or not available",
                title="🎮 GPU",
                border_style="red"
            ))
        
        # Thermal state (if available)
        thermal_state = system_info.get("thermal_state")
        if thermal_state:
            color = "green" if thermal_state == "nominal" else "yellow" if thermal_state == "fair" else "red"
            console.print(Panel(
                f"State: {thermal_state.title()}",
                title="🌡️  Thermal",
                border_style=color
            ))
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.pass_context
def validate(ctx, verbose, quiet, config):
    """Validate system environment for ehAye."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        console.print("🔬 System Environment Validation")
        console.print("=" * 50)
        
        issues = []
        
        # Python version check
        try:
            import sys
            if sys.version_info >= (3, 10):
                console.print("✅ Python version: OK")
            else:
                raise Exception(f"Python {sys.version_info.major}.{sys.version_info.minor} found, 3.10+ required")
        except Exception as e:
            console.print(f"❌ Python version: {e}")
            issues.append("Python version")
        
        # Virtual environment check
        try:
            import os
            venv_path = os.environ.get('VIRTUAL_ENV')
            if venv_path:
                console.print("✅ Virtual environment: OK")
            else:
                raise Exception("Not running in a virtual environment")
        except Exception as e:
            console.print(f"❌ Virtual environment: {e}")
            issues.append("Virtual environment")
        
        # System resources check
        try:
            # Basic memory check
            import psutil
            memory = psutil.virtual_memory()
            if memory.total >= 8 * 1024**3:  # 8GB minimum
                console.print("✅ System resources: OK")
            else:
                raise Exception(f"Only {memory.total/1024**3:.1f}GB RAM available, 8GB+ recommended")
        except ImportError:
            console.print("❌ System resources: psutil not available")
            issues.append("System resources")
        except Exception as e:
            console.print(f"❌ System resources: {e}")
            issues.append("System resources")
        
        # Package availability
        required_packages = ["mlx_lm", "psutil", "rich", "click"]
        missing_packages = []
        for pkg in required_packages:
            try:
                __import__(pkg)
            except ImportError:
                missing_packages.append(pkg)
        
        if missing_packages:
            console.print(f"❌ Missing packages: {', '.join(missing_packages)}")
            issues.append("Required packages")
        else:
            console.print("✅ Required packages: OK")
        
        # Benchmark environment
        if validate_benchmark_environment():
            console.print("✅ Benchmark environment: OK")
        else:
            console.print("❌ Benchmark environment: Issues detected")
            issues.append("Benchmark environment")
        
        # Summary
        if issues:
            console.print(f"\n❌ Validation completed with {len(issues)} issue(s)")
            console.print("Issues found in:")
            for issue in issues:
                console.print(f"  • {issue}")
        else:
            console.print("\n✅ All validation checks passed!")
            show_success("System is ready for ehAye")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.option("--paths", is_flag=True, help="Show configured paths")
@click.option("--env", is_flag=True, help="Show environment variables")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.pass_context
def config(ctx, paths, env, verbose, quiet, config):
    """Show configuration information."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        config = get_config()
        
        console.print("⚙️ Configuration")
        console.print("=" * 50)
        
        if paths or not (env):
            # Show paths
            console.print("\n📁 Configured Paths:")
            table = Table(show_header=False)
            table.add_column("Path", style="bold blue")
            table.add_column("Location")
            
            table.add_row("Cache Directory", str(config.paths.cache_dir))
            table.add_row("Models Directory", str(config.paths.models_dir))
            table.add_row("Logs Directory", str(config.paths.logs_dir))
            table.add_row("Config Directory", str(config.paths.config_dir))
            
            console.print(table)
        
        if env or not (paths):
            # Show environment variables
            console.print("\n🌍 Environment Variables:")
            table = Table(show_header=False)
            table.add_column("Variable", style="bold green")
            table.add_column("Value")
            
            for var, value in config.environment_variables.items():
                table.add_row(var, value)
            
            console.print(table)
        
        # Show performance settings
        console.print("\n⚡ Performance Settings:")
        perf_table = Table(show_header=False)
        perf_table.add_column("Setting", style="bold yellow")
        perf_table.add_column("Value")
        
        perf_table.add_row("OMP Threads", str(config.performance.omp_num_threads))
        perf_table.add_row("MLX Memory Pool", "Enabled" if config.performance.mlx_memory_pool else "Disabled")
        perf_table.add_row("Max Cache Size", f"{config.performance.max_cache_size_gb}GB")
        
        console.print(perf_table)
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.option("--force", "-f", is_flag=True, help="Force setup even if directories exist")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.pass_context
def setup(ctx, force, verbose, quiet, config):
    """Set up system directories and environment."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config)
        
        console.print("🔧 System Setup")
        console.print("=" * 50)
        
        config = get_config()
        
        # Create directories
        show_info("Creating directories...")
        config.create_directories()
        show_success("Directories created")
        
        # Set up environment variables
        show_info("Setting up environment...")
        config.setup_environment()
        show_success("Environment configured")
        
        console.print("\n✅ System setup completed!")
        console.print("\n💡 Next steps:")
        console.print("  1. Install models: ali mod search")
        console.print("  2. Start chatting: ali chat interactive")
        console.print("  3. Run benchmarks: ali perf validate")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


@app.command()
@click.option("--logs", is_flag=True, help="Clean up log files")
@click.option("--cache", is_flag=True, help="Clean up cache files")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Quiet mode")
@click.option("--config", type=click.Path(exists=True), help="Config file")
@click.pass_context
def cleanup(ctx, logs, cache, force, verbose, quiet, config):
    """Clean up system files and caches."""
    try:
        base_cli = common_setup(ctx, verbose, quiet, config, skip_venv=True)
        
        if not (logs or cache):
            show_error("Specify what to clean: --logs, --cache, or both")
            return
        
        from ..configuration import get_config
        config = get_config()
        
        # Confirm action
        if not force:
            actions = []
            if logs:
                actions.append("log files")
            if cache:
                actions.append("cache files")
            
            if not click.confirm(f"Clean up {' and '.join(actions)}?"):
                return
        
        # Clean logs
        if logs:
            show_info("Cleaning log files...")
            logs_dir = config.paths.logs_dir
            if logs_dir.exists():
                import shutil
                shutil.rmtree(logs_dir)
                logs_dir.mkdir(parents=True, exist_ok=True)
                show_success("Log files cleaned")
            else:
                show_info("No log files to clean")
        
        # Clean cache
        if cache:
            show_info("Cleaning cache files...")
            cache_dir = config.paths.cache_dir
            if cache_dir.exists():
                # Don't remove models, just other cache
                for item in cache_dir.iterdir():
                    if item.name != "models":
                        if item.is_dir():
                            import shutil
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                show_success("Cache files cleaned (models preserved)")
            else:
                show_info("No cache files to clean")
        
        console.print("🧹 Cleanup completed!")
        
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        base_cli.handle_error(e)


def main():
    """Main entry point for system CLI."""
    try:
        app()
    except KeyboardInterrupt:
        handle_keyboard_interrupt()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()