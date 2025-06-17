"""Custom logging handlers for ehAye."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, TextIO

from rich.console import Console


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Enhanced rotating file handler with better error handling."""
    
    def __init__(self, filename: Path, max_bytes: int = 10*1024*1024, backup_count: int = 5):
        # Ensure parent directory exists
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(
            filename=str(filename),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    
    def emit(self, record):
        """Emit a record with enhanced error handling."""
        try:
            super().emit(record)
        except Exception as e:
            # If file logging fails, fall back to stderr
            print(f"Logging error: {e}", file=sys.stderr)
            print(self.format(record), file=sys.stderr)


class StreamHandler(logging.StreamHandler):
    """Enhanced stream handler with colored output."""
    
    def __init__(self, stream: Optional[TextIO] = None, use_colors: bool = True):
        super().__init__(stream)
        self.use_colors = use_colors
        self.console = Console(file=stream or sys.stdout)
    
    def emit(self, record):
        """Emit a record with optional color formatting."""
        try:
            msg = self.format(record)
            
            if self.use_colors and hasattr(self.console, 'print'):
                # Use rich console for colored output
                level_colors = {
                    'DEBUG': 'dim white',
                    'INFO': 'blue',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold red'
                }
                color = level_colors.get(record.levelname, 'white')
                self.console.print(msg, style=color)
            else:
                self.stream.write(msg)
                self.stream.write(self.terminator)
            
            self.flush()
        except Exception:
            self.handleError(record)


class MemoryHandler(logging.handlers.MemoryHandler):
    """Memory handler for buffering log records."""
    
    def __init__(self, capacity: int = 1000, flush_level: int = logging.ERROR):
        # Create a null handler as the target initially
        target = logging.NullHandler()
        super().__init__(capacity, flushLevel=flush_level, target=target)
    
    def set_target(self, target: logging.Handler) -> None:
        """Set the target handler for flushing."""
        self.target = target
    
    def should_flush(self, record):
        """Determine if the buffer should be flushed."""
        return (len(self.buffer) >= self.capacity) or (record.levelno >= self.flushLevel)


class AsyncHandler(logging.Handler):
    """Asynchronous logging handler for high-performance scenarios."""
    
    def __init__(self, target_handler: logging.Handler, queue_size: int = 1000):
        super().__init__()
        self.target_handler = target_handler
        self.queue_size = queue_size
        self._queue = []
        self._enabled = True
    
    def emit(self, record):
        """Emit a record asynchronously."""
        if not self._enabled:
            return
        
        try:
            # Add to queue
            if len(self._queue) < self.queue_size:
                self._queue.append(record)
            else:
                # Queue is full, process immediately
                self._flush_queue()
                self._queue.append(record)
        except Exception:
            self.handleError(record)
    
    def _flush_queue(self):
        """Flush all queued records to the target handler."""
        while self._queue:
            record = self._queue.pop(0)
            try:
                self.target_handler.emit(record)
            except Exception:
                self.target_handler.handleError(record)
    
    def close(self):
        """Close the handler and flush any remaining records."""
        self._flush_queue()
        self.target_handler.close()
        super().close()
    
    def disable(self):
        """Disable the handler."""
        self._enabled = False