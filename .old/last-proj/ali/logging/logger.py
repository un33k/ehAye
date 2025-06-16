"""Enhanced logging configuration for ehAye Local."""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.logging import RichHandler

from .handlers import RotatingFileHandler
from .formatters import ColorFormatter, DetailedFormatter


class EhAyeLogger:
    """Centralized logging configuration with enhanced features."""
    
    def __init__(self, name: str = "ehaye"):
        self.name = name
        self.console = Console()
        self._logger: Optional[logging.Logger] = None
        self._configured_loggers: Dict[str, logging.Logger] = {}
    
    def setup(
        self,
        level: str = "INFO",
        log_file: Optional[Path] = None,
        enable_rich: bool = True,
        enable_file_rotation: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        json_logging: bool = False
    ) -> logging.Logger:
        """Set up logging configuration with enhanced options."""
        if self._logger:
            return self._logger
        
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Console handler
        if enable_rich:
            console_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
                tracebacks_show_locals=False
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColorFormatter())
        
        console_handler.setLevel(getattr(logging, level.upper()))
        self._logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            if enable_file_rotation:
                file_handler = RotatingFileHandler(
                    log_file,
                    max_bytes=max_file_size,
                    backup_count=backup_count
                )
            else:
                file_handler = logging.FileHandler(log_file)
            
            if json_logging:
                from .formatters import JSONFormatter
                file_formatter = JSONFormatter()
            else:
                file_formatter = DetailedFormatter()
            
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            self._logger.addHandler(file_handler)
        
        return self._logger
    
    def get_child_logger(self, name: str, level: Optional[str] = None) -> logging.Logger:
        """Get a child logger with specific configuration."""
        full_name = f"{self.name}.{name}"
        
        if full_name in self._configured_loggers:
            return self._configured_loggers[full_name]
        
        child_logger = logging.getLogger(full_name)
        
        if level:
            child_logger.setLevel(getattr(logging, level.upper()))
        elif self._logger:
            child_logger.setLevel(self._logger.level)
        
        # Child loggers inherit handlers from parent
        child_logger.propagate = True
        
        self._configured_loggers[full_name] = child_logger
        return child_logger
    
    def add_context_filter(self, context: Dict[str, Any]) -> None:
        """Add context information to all log records."""
        class ContextFilter(logging.Filter):
            def filter(self, record):
                for key, value in context.items():
                    setattr(record, key, value)
                return True
        
        if self._logger:
            self._logger.addFilter(ContextFilter())
    
    def set_level(self, level: str) -> None:
        """Change the logging level."""
        if self._logger:
            self._logger.setLevel(getattr(logging, level.upper()))
            
            # Update handler levels
            for handler in self._logger.handlers:
                if isinstance(handler, (logging.StreamHandler, RichHandler)):
                    handler.setLevel(getattr(logging, level.upper()))
    
    def disable_external_loggers(self, loggers: Optional[list[str]] = None) -> None:
        """Disable or quiet external library loggers."""
        if loggers is None:
            loggers = [
                "urllib3",
                "requests",
                "httpx",
                "transformers",
                "huggingface_hub",
                "torch",
                "mlx",
            ]
        
        for logger_name in loggers:
            external_logger = logging.getLogger(logger_name)
            external_logger.setLevel(logging.WARNING)
            external_logger.propagate = False
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance."""
        if not self._logger:
            return self.setup()
        return self._logger
    
    def configure_performance_logging(self, enabled: bool = True) -> None:
        """Configure performance-related logging."""
        perf_logger = self.get_child_logger("performance")
        
        if enabled:
            perf_logger.setLevel(logging.DEBUG)
            
            # Add performance-specific handler if needed
            perf_file = Path("logs/performance.log")
            if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(perf_file) 
                      for h in perf_logger.handlers):
                perf_handler = logging.FileHandler(perf_file)
                perf_handler.setFormatter(DetailedFormatter())
                perf_logger.addHandler(perf_handler)
        else:
            perf_logger.setLevel(logging.WARNING)


# Global logger instance
ehaye_logger = EhAyeLogger()


def get_logger(name: str = "ehaye") -> logging.Logger:
    """Get a logger instance."""
    if name == "ehaye":
        return ehaye_logger.logger
    
    return ehaye_logger.get_child_logger(name)