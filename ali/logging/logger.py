"""Logging configuration for ehAye."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


class EhAyeLogger:
    """Centralized logging configuration."""
    
    def __init__(self, name: str = "ehaye"):
        self.name = name
        self.console = Console()
        self._logger: Optional[logging.Logger] = None
    
    def setup(
        self,
        level: str = "INFO",
        log_file: Optional[Path] = None,
        enable_rich: bool = True
    ) -> logging.Logger:
        """Set up logging configuration."""
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
                markup=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(formatter)
        
        console_handler.setLevel(getattr(logging, level.upper()))
        self._logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)
            self._logger.addHandler(file_handler)
        
        return self._logger
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance."""
        if not self._logger:
            return self.setup()
        return self._logger


# Global logger instance
ehaye_logger = EhAyeLogger()


def get_logger(name: str = "ehaye") -> logging.Logger:
    """Get a logger instance."""
    if name == "ehaye":
        return ehaye_logger.logger
    
    # Child logger
    child_logger = logging.getLogger(f"ehaye.{name}")
    if not child_logger.handlers:
        child_logger.setLevel(ehaye_logger.logger.level)
        child_logger.addHandler(logging.NullHandler())
    
    return child_logger