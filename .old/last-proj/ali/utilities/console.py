"""Console and rich output utilities."""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from rich.console import Console
from rich.progress import (
    Progress,
    TaskID,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
    DownloadColumn,
    TransferSpeedColumn
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.status import Status


class ConsoleManager:
    """Manages console output and rich formatting."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._progress: Optional[Progress] = None
        self._live: Optional[Live] = None
    
    def print(self, *args, **kwargs) -> None:
        """Print with rich formatting."""
        self.console.print(*args, **kwargs)
    
    def error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"❌ {message}", style="bold red")
    
    def success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"✅ {message}", style="bold green")
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"⚠️  {message}", style="bold yellow")
    
    def info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"ℹ️  {message}", style="bold blue")
    
    def create_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "blue",
        expand: bool = True
    ) -> Panel:
        """Create a rich panel."""
        return Panel(
            content,
            title=title,
            border_style=style,
            expand=expand
        )
    
    def create_table(
        self,
        headers: List[str],
        rows: List[List[str]],
        title: Optional[str] = None,
        show_lines: bool = True
    ) -> Table:
        """Create a rich table."""
        table = Table(title=title, show_lines=show_lines)
        
        for header in headers:
            table.add_column(header, style="cyan", no_wrap=True)
        
        for row in rows:
            table.add_row(*row)
        
        return table
    
    def status(self, message: str, spinner: str = "dots") -> Status:
        """Create a status spinner."""
        return self.console.status(message, spinner=spinner)
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """Ask for user confirmation."""
        from rich.prompt import Confirm
        return Confirm.ask(message, default=default, console=self.console)
    
    def prompt(self, message: str, default: Optional[str] = None) -> str:
        """Get user input."""
        from rich.prompt import Prompt
        return Prompt.ask(message, default=default, console=self.console)
    
    def choice(
        self,
        message: str,
        choices: List[str],
        default: Optional[str] = None
    ) -> str:
        """Get user choice from options."""
        from rich.prompt import Prompt
        choices_str = "/".join(choices)
        prompt_msg = f"{message} [{choices_str}]"
        
        while True:
            response = self.prompt(prompt_msg, default)
            if response in choices:
                return response
            self.error(f"Invalid choice. Please select from: {choices_str}")


def create_progress(download: bool = False) -> Progress:
    """Create a progress bar with appropriate columns."""
    if download:
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=Console()
        )
    else:
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=Console()
        )


def create_table(
    headers: List[str],
    rows: List[List[str]],
    title: Optional[str] = None,
    style: str = "blue"
) -> Table:
    """Create a formatted table."""
    table = Table(title=title, style=style)
    
    for header in headers:
        table.add_column(header, style="cyan")
    
    for row in rows:
        table.add_row(*row)
    
    return table


def format_bytes(bytes_value: Union[int, float]) -> str:
    """Format bytes in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def create_status_layout(
    status_text: str,
    details: Optional[Dict[str, Any]] = None
) -> Layout:
    """Create a status layout with optional details."""
    layout = Layout()
    
    # Main status
    status_panel = Panel(
        Text(status_text, style="bold green"),
        title="Status",
        border_style="green"
    )
    
    if details:
        # Create details table
        detail_rows = []
        for key, value in details.items():
            detail_rows.append([key.replace("_", " ").title(), str(value)])
        
        details_table = create_table(["Property", "Value"], detail_rows)
        details_panel = Panel(details_table, title="Details", border_style="blue")
        
        layout.split_column(
            Layout(status_panel, size=3),
            Layout(details_panel)
        )
    else:
        layout.update(status_panel)
    
    return layout


def display_model_info(model_data: Dict[str, Any], console: Optional[Console] = None) -> None:
    """Display model information in a formatted way."""
    if console is None:
        console = Console()
    
    # Create main info table
    info_rows = []
    for key, value in model_data.items():
        if key not in ['parameters', 'tags', 'files']:
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, (int, float)) and key.endswith(('_size', '_bytes')):
                formatted_value = format_bytes(value)
            else:
                formatted_value = str(value)
            info_rows.append([formatted_key, formatted_value])
    
    info_table = create_table(["Property", "Value"], info_rows, title="Model Information")
    console.print(info_table)
    
    # Display parameters if available
    if 'parameters' in model_data and model_data['parameters']:
        param_rows = []
        for param, value in model_data['parameters'].items():
            param_rows.append([param, str(value)])
        
        param_table = create_table(["Parameter", "Value"], param_rows, title="Parameters")
        console.print("\n", param_table)
    
    # Display tags if available
    if 'tags' in model_data and model_data['tags']:
        tags_text = ", ".join(model_data['tags'])
        tags_panel = Panel(tags_text, title="Tags", border_style="yellow")
        console.print("\n", tags_panel)


def create_comparison_table(
    data: List[Dict[str, Any]],
    columns: List[str],
    title: str = "Comparison"
) -> Table:
    """Create a comparison table for multiple items."""
    table = Table(title=title, show_lines=True)
    
    # Add columns
    for col in columns:
        table.add_column(col.replace("_", " ").title(), style="cyan")
    
    # Add rows
    for item in data:
        row = []
        for col in columns:
            value = item.get(col, "N/A")
            if isinstance(value, (int, float)) and col.endswith(('_size', '_bytes')):
                value = format_bytes(value)
            elif isinstance(value, float) and col.endswith('_time'):
                value = format_duration(value)
            row.append(str(value))
        table.add_row(*row)
    
    return table