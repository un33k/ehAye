"""Custom logging formatters for ehAye."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict


class ColorFormatter(logging.Formatter):
    """Formatter with color support for terminal output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green  
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, use_colors: bool = None):
        super().__init__()
        if use_colors is None:
            # Auto-detect color support
            self.use_colors = sys.stdout.isatty() and sys.platform != 'win32'
        else:
            self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the record with optional colors."""
        # Create a copy of the record to avoid modifying the original
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Basic format
        timestamp = datetime.fromtimestamp(record_copy.created).strftime('%H:%M:%S')
        level = record_copy.levelname
        name = record_copy.name
        message = record_copy.getMessage()
        
        if self.use_colors:
            color = self.COLORS.get(level, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            formatted = f"{color}[{timestamp}] {level:8} {name}: {message}{reset}"
        else:
            formatted = f"[{timestamp}] {level:8} {name}: {message}"
        
        # Add exception info if present
        if record_copy.exc_info:
            formatted += '\n' + self.formatException(record_copy.exc_info)
        
        return formatted


class DetailedFormatter(logging.Formatter):
    """Detailed formatter for file logging."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the record with detailed information."""
        # Add thread info if available
        if hasattr(record, 'thread'):
            record.thread_name = getattr(record, 'threadName', 'MainThread')
        
        formatted = super().format(record)
        
        # Add exception info with full traceback
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        return formatted


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the record as JSON."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add thread information
        if hasattr(record, 'thread'):
            log_data['thread'] = record.thread
            log_data['thread_name'] = getattr(record, 'threadName', 'MainThread')
        
        # Add process information
        if hasattr(record, 'process'):
            log_data['process'] = record.process
        
        # Add exception information
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields
        if self.include_extra:
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in {
                    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                    'filename', 'module', 'lineno', 'funcName', 'created', 
                    'msecs', 'relativeCreated', 'thread', 'threadName', 
                    'processName', 'process', 'stack_info', 'exc_info', 'exc_text'
                }:
                    extra_fields[key] = value
            
            if extra_fields:
                log_data['extra'] = extra_fields
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class CompactFormatter(logging.Formatter):
    """Compact formatter for minimal output."""
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the record compactly."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level_short = record.levelname[:1]  # Just first letter
        message = record.getMessage()
        
        # Show module name only if it's not the main logger
        if record.name != 'ehaye':
            module_name = record.name.split('.')[-1]  # Last part of the name
            return f"{timestamp} {level_short} {module_name}: {message}"
        else:
            return f"{timestamp} {level_short} {message}"


class PerformanceFormatter(logging.Formatter):
    """Formatter optimized for performance logging."""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S.%f'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the record for performance analysis."""
        formatted = super().format(record)
        
        # Add timing information if available
        if hasattr(record, 'duration'):
            formatted += f' | Duration: {record.duration:.4f}s'
        
        if hasattr(record, 'memory_usage'):
            formatted += f' | Memory: {record.memory_usage:.2f}MB'
        
        return formatted