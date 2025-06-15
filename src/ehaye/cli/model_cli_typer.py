"""Model management CLI interface using typer."""

from typing import Optional
import typer
from rich.console import Console

console = Console()

app = typer.Typer(name="mod", help="Model management and installation")


@app.command()
def list(
    provider: Optional[str] = typer.Option("ollama", "--provider", "-p", help="Provider to use"),
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Debug output"),
):
    """List installed models."""
    from .model_cli import main as model_main
    import sys
    
    # Reconstruct argv for the legacy model CLI
    sys.argv = ["ali"] + ["-l"] + \
              (["--provider", provider] if provider != "ollama" else []) + \
              (["-q", query] if query else []) + \
              (["-c", category] if category else []) + \
              (["-v"] if verbose else []) + \
              (["--debug"] if debug else [])
    model_main()


@app.command()
def search(
    query: Optional[str] = typer.Option(None, "--query", "-q", help="Search query"),
    provider: Optional[str] = typer.Option("ollama", "--provider", "-p", help="Provider to use"),
    flavor: Optional[str] = typer.Option(None, "--flavor", "-f", help="Model flavor/size"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Debug output"),
):
    """Search available models."""
    from .model_cli import main as model_main
    import sys
    
    sys.argv = ["ali"] + ["-s"] + \
              (["-q", query] if query else []) + \
              (["--provider", provider] if provider != "ollama" else []) + \
              (["-f", flavor] if flavor else []) + \
              (["-v"] if verbose else []) + \
              (["--debug"] if debug else [])
    model_main()


@app.command()
def download(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model ID to download"),
    provider: Optional[str] = typer.Option("ollama", "--provider", "-p", help="Provider to use"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive selection"),
    force: bool = typer.Option(False, "--force", help="Force download"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Debug output"),
):
    """Download a model."""
    from .model_cli import main as model_main
    import sys
    
    sys.argv = ["ali"] + ["-d"] + \
              (["-m", model] if model else []) + \
              (["--provider", provider] if provider != "ollama" else []) + \
              (["--interactive"] if interactive else []) + \
              (["--force"] if force else []) + \
              (["-v"] if verbose else []) + \
              (["--debug"] if debug else [])
    model_main()


@app.command()
def remove(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model ID to remove"),
    provider: Optional[str] = typer.Option("ollama", "--provider", "-p", help="Provider to use"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive selection"),
    force: bool = typer.Option(False, "--force", help="Force removal"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Debug output"),
):
    """Remove a model."""
    from .model_cli import main as model_main
    import sys
    
    sys.argv = ["ali"] + ["-r"] + \
              (["-m", model] if model else []) + \
              (["--provider", provider] if provider != "ollama" else []) + \
              (["--interactive"] if interactive else []) + \
              (["--force"] if force else []) + \
              (["-v"] if verbose else []) + \
              (["--debug"] if debug else [])
    model_main()


@app.command()
def info(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model ID to show info for"),
    provider: Optional[str] = typer.Option("ollama", "--provider", "-p", help="Provider to use"),
    interactive: bool = typer.Option(False, "--interactive", help="Interactive selection"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Debug output"),
):
    """Show model information."""
    from .model_cli import main as model_main
    import sys
    
    sys.argv = ["ali"] + ["-i"] + \
              (["-m", model] if model else []) + \
              (["--provider", provider] if provider != "ollama" else []) + \
              (["--interactive"] if interactive else []) + \
              (["-v"] if verbose else []) + \
              (["--debug"] if debug else [])
    model_main()


def main():
    """Main entry point for model CLI."""
    app()


if __name__ == "__main__":
    main()