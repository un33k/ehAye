"""Logging utility functions."""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional

from .logger import get_logger


@contextmanager
def timed_operation(operation_name: str, logger: Optional[logging.Logger] = None):
    """Context manager for timing operations."""
    if logger is None:
        logger = get_logger("performance")
    
    start_time = time.time()
    logger.debug(f"Starting {operation_name}")
    
    try:
        yield
        duration = time.time() - start_time
        logger.info(f"Completed {operation_name} in {duration:.4f}s", extra={'duration': duration})
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed {operation_name} after {duration:.4f}s: {e}", extra={'duration': duration})
        raise


def log_performance(operation_name: Optional[str] = None, logger: Optional[logging.Logger] = None):
    """Decorator for logging function performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            nonlocal operation_name
            if operation_name is None:
                operation_name = f"{func.__module__}.{func.__name__}"
            
            perf_logger = logger or get_logger("performance")
            
            with timed_operation(operation_name, perf_logger):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_method_calls(cls):
    """Class decorator to log all method calls."""
    class_logger = get_logger(f"calls.{cls.__name__}")
    
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, log_performance(f"{cls.__name__}.{attr_name}", class_logger)(attr))
    
    return cls


def configure_silence_external_loggers():
    """Configure external library loggers to reduce noise."""
    external_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool', 
        'transformers',
        'huggingface_hub',
        'torch',
        'mlx',
        'httpx',
        'asyncio',
    ]
    
    for logger_name in external_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def create_logger_with_context(name: str, context: dict) -> logging.Logger:
    """Create a logger with persistent context information."""
    logger = get_logger(name)
    
    class ContextFilter(logging.Filter):
        def filter(self, record):
            for key, value in context.items():
                setattr(record, key, value)
            return True
    
    logger.addFilter(ContextFilter())
    return logger


def log_exception(logger: logging.Logger, exception: Exception, context: Optional[dict] = None):
    """Log an exception with optional context."""
    extra = context or {}
    extra.update({
        'exception_type': type(exception).__name__,
        'exception_args': exception.args,
    })
    
    logger.exception(f"Exception occurred: {exception}", extra=extra)


def setup_debug_logging(enable: bool = True):
    """Enable or disable debug logging across the application."""
    root_logger = logging.getLogger("ehaye")
    
    if enable:
        root_logger.setLevel(logging.DEBUG)
        # Enable debug for specific modules
        debug_modules = ["configuration", "backends", "models", "chat"]
        for module in debug_modules:
            get_logger(module).setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


def get_logging_stats() -> dict:
    """Get statistics about logging activity."""
    stats = {
        'loggers': {},
        'handlers': {},
        'total_records': 0,
    }
    
    # Collect information about all loggers
    for name, logger in logging.Logger.manager.loggerDict.items():
        if isinstance(logger, logging.Logger):
            stats['loggers'][name] = {
                'level': logger.level,
                'handlers': len(logger.handlers),
                'disabled': logger.disabled,
            }
    
    # Collect handler information
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler_type = type(handler).__name__
        if handler_type not in stats['handlers']:
            stats['handlers'][handler_type] = 0
        stats['handlers'][handler_type] += 1
    
    return stats