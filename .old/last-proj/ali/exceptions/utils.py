"""Exception handling utilities."""

import logging
import sys
import traceback
from typing import Any, Dict, List, Optional, Type, Union

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .base import EhAyeError, EhAyeWarning


def handle_exception(
    exception: Exception,
    logger: Optional[logging.Logger] = None,
    console: Optional[Console] = None,
    show_traceback: bool = False,
    exit_on_error: bool = False,
    exit_code: int = 1
) -> None:
    """Handle exceptions with appropriate logging and user feedback."""
    if logger is None:
        logger = logging.getLogger("ehaye.exceptions")
    
    if console is None:
        console = Console(stderr=True)
    
    if isinstance(exception, EhAyeError):
        # Handle our custom exceptions
        _handle_ehaye_error(exception, logger, console, show_traceback)
    else:
        # Handle standard exceptions
        _handle_standard_exception(exception, logger, console, show_traceback)
    
    if exit_on_error:
        sys.exit(exit_code)


def _handle_ehaye_error(
    error: EhAyeError,
    logger: logging.Logger,
    console: Console,
    show_traceback: bool
) -> None:
    """Handle EhAye-specific errors."""
    # Log the error
    logger.error(f"{error.__class__.__name__}: {error.message}", extra=error.context)
    
    # Display user-friendly error
    error_panel = Panel(
        Text(str(error), style="red"),
        title=f"❌ {error.__class__.__name__}",
        border_style="red"
    )
    console.print(error_panel)
    
    # Show context if available
    if error.context:
        context_lines = []
        for key, value in error.context.items():
            context_lines.append(f"{key}: {value}")
        
        if context_lines:
            console.print("\n[dim]Context:[/dim]")
            for line in context_lines:
                console.print(f"  {line}", style="dim")
    
    # Show suggestions if available
    if "suggestion" in error.context:
        console.print(f"\n[green]💡 Suggestion:[/green] {error.context['suggestion']}")
    
    # Show traceback if requested
    if show_traceback:
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc(), style="dim")


def _handle_standard_exception(
    exception: Exception,
    logger: logging.Logger,
    console: Console,
    show_traceback: bool
) -> None:
    """Handle standard Python exceptions."""
    # Log the exception
    logger.exception(f"Unhandled exception: {exception}")
    
    # Display user-friendly error
    error_panel = Panel(
        Text(str(exception), style="red"),
        title=f"❌ {exception.__class__.__name__}",
        border_style="red"
    )
    console.print(error_panel)
    
    # Always show traceback for unhandled exceptions if requested
    if show_traceback:
        console.print("\n[dim]Traceback:[/dim]")
        console.print(traceback.format_exc(), style="dim")


def format_exception(
    exception: Exception,
    include_traceback: bool = False,
    include_context: bool = True
) -> str:
    """Format an exception for display or logging."""
    lines = []
    
    # Basic exception info
    lines.append(f"{exception.__class__.__name__}: {exception}")
    
    # Add context for EhAye errors
    if isinstance(exception, EhAyeError) and include_context and exception.context:
        lines.append("Context:")
        for key, value in exception.context.items():
            lines.append(f"  {key}: {value}")
    
    # Add traceback if requested
    if include_traceback:
        lines.append("\nTraceback:")
        lines.append(traceback.format_exc())
    
    return "\n".join(lines)


def create_error_context(**kwargs) -> Dict[str, Any]:
    """Create a standardized error context dictionary."""
    context = {}
    
    # Add common context fields
    for key, value in kwargs.items():
        if value is not None:
            context[key] = value
    
    # Add system information if not already present
    if "python_version" not in context:
        context["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    return context


def chain_exceptions(
    primary_exception: Exception,
    secondary_exceptions: List[Exception]
) -> EhAyeError:
    """Chain multiple exceptions into a single EhAye error."""
    messages = [str(primary_exception)]
    messages.extend(str(exc) for exc in secondary_exceptions)
    
    combined_message = "; ".join(messages)
    context = {
        "primary_exception": primary_exception.__class__.__name__,
        "secondary_exceptions": [exc.__class__.__name__ for exc in secondary_exceptions],
        "exception_count": len(secondary_exceptions) + 1,
    }
    
    return EhAyeError(combined_message, context=context, cause=primary_exception)


def wrap_exception(
    exception: Exception,
    wrapper_class: Type[EhAyeError],
    message: Optional[str] = None,
    **context_kwargs
) -> EhAyeError:
    """Wrap a standard exception in an EhAye error."""
    if message is None:
        message = str(exception)
    
    context = create_error_context(**context_kwargs)
    context["original_exception"] = exception.__class__.__name__
    
    return wrapper_class(message, context=context, cause=exception)


def is_user_error(exception: Exception) -> bool:
    """Determine if an exception is likely a user error (vs system error)."""
    user_error_types = (
        FileNotFoundError,
        PermissionError,
        ValueError,
        KeyError,
    )
    
    if isinstance(exception, user_error_types):
        return True
    
    if isinstance(exception, EhAyeError):
        # Check if it's a user-facing error type
        user_error_classes = [
            "ArgumentError",
            "ValidationError", 
            "ModelNotFoundError",
            "ConfigurationError",
        ]
        return exception.__class__.__name__ in user_error_classes
    
    return False


def suggest_fix(exception: Exception) -> Optional[str]:
    """Suggest a fix for common exceptions."""
    if isinstance(exception, FileNotFoundError):
        return f"Check if the file exists: {exception.filename}"
    
    if isinstance(exception, PermissionError):
        return "Check file permissions or run with appropriate privileges"
    
    if isinstance(exception, ImportError):
        missing_module = str(exception).split("'")[1] if "'" in str(exception) else "module"
        return f"Install the missing module: pip install {missing_module}"
    
    if isinstance(exception, ConnectionError):
        return "Check network connectivity and service availability"
    
    if isinstance(exception, EhAyeError) and "suggestion" in exception.context:
        return exception.context["suggestion"]
    
    return None


def format_error_for_user(exception: Exception) -> str:
    """Format an error message for end users (non-technical)."""
    if isinstance(exception, EhAyeError):
        message = exception.message
    else:
        message = str(exception)
    
    # Remove technical details
    message = message.replace("__", "")
    message = message.replace("_", " ")
    
    # Add suggestion if available
    suggestion = suggest_fix(exception)
    if suggestion:
        message += f"\n\nSuggestion: {suggestion}"
    
    return message


def collect_exception_stats(exceptions: List[Exception]) -> Dict[str, Any]:
    """Collect statistics about a list of exceptions."""
    stats = {
        "total_count": len(exceptions),
        "by_type": {},
        "user_errors": 0,
        "system_errors": 0,
        "ehaye_errors": 0,
        "standard_errors": 0,
    }
    
    for exc in exceptions:
        exc_type = exc.__class__.__name__
        
        # Count by type
        if exc_type not in stats["by_type"]:
            stats["by_type"][exc_type] = 0
        stats["by_type"][exc_type] += 1
        
        # Categorize errors
        if is_user_error(exc):
            stats["user_errors"] += 1
        else:
            stats["system_errors"] += 1
        
        if isinstance(exc, EhAyeError):
            stats["ehaye_errors"] += 1
        else:
            stats["standard_errors"] += 1
    
    return stats