"""Utility decorators for common patterns."""

import functools
import time
import threading
from typing import Any, Callable, Dict, Optional, TypeVar, Union
import warnings

from ..exceptions import EhAyeError
from ..logging import get_logger

logger = get_logger("utilities.decorators")

F = TypeVar('F', bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable[[F], F]:
    """Retry decorator with exponential backoff."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.debug(f"Attempt {attempt} failed for {func.__name__}: {e}")
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            return None  # Should never reach here
        
        return wrapper
    return decorator


def timeout(seconds: float) -> Callable[[F], F]:
    """Timeout decorator for functions."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                # Note: We can't actually kill the thread in Python
                # This is a limitation of the timeout decorator
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator


def log_execution_time(
    logger_name: Optional[str] = None,
    level: str = "DEBUG",
    include_args: bool = False
) -> Callable[[F], F]:
    """Log function execution time."""
    def decorator(func: F) -> F:
        func_logger = get_logger(logger_name or f"timing.{func.__module__}.{func.__name__}")
        log_level = getattr(func_logger, level.lower())
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                if include_args:
                    log_level(
                        f"{func.__name__}({args}, {kwargs}) completed in {execution_time:.4f}s"
                    )
                else:
                    log_level(f"{func.__name__} completed in {execution_time:.4f}s")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                log_level(f"{func.__name__} failed after {execution_time:.4f}s: {e}")
                raise
        
        return wrapper
    return decorator


def cache_result(
    max_size: int = 128,
    ttl: Optional[float] = None,
    key_func: Optional[Callable] = None
) -> Callable[[F], F]:
    """Cache function results with optional TTL."""
    def decorator(func: F) -> F:
        cache: Dict[str, Dict[str, Any]] = {}
        cache_lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = str(hash((args, tuple(sorted(kwargs.items())))))
            
            current_time = time.time()
            
            with cache_lock:
                # Check if result is cached and valid
                if cache_key in cache:
                    cached_data = cache[cache_key]
                    
                    # Check TTL
                    if ttl is None or (current_time - cached_data['timestamp']) < ttl:
                        logger.debug(f"Cache hit for {func.__name__} with key {cache_key}")
                        return cached_data['result']
                    else:
                        # Expired, remove from cache
                        del cache[cache_key]
                
                # Cache miss or expired, compute result
                logger.debug(f"Cache miss for {func.__name__} with key {cache_key}")
                result = func(*args, **kwargs)
                
                # Store in cache
                cache[cache_key] = {
                    'result': result,
                    'timestamp': current_time
                }
                
                # Evict oldest entries if cache is full
                if len(cache) > max_size:
                    oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'])
                    del cache[oldest_key]
                
                return result
        
        # Add cache control methods
        def clear_cache():
            with cache_lock:
                cache.clear()
        
        def cache_info():
            with cache_lock:
                return {
                    'cache_size': len(cache),
                    'max_size': max_size,
                    'ttl': ttl,
                    'keys': list(cache.keys())
                }
        
        wrapper.clear_cache = clear_cache
        wrapper.cache_info = cache_info
        
        return wrapper
    return decorator


def deprecated(
    reason: str = "",
    version: Optional[str] = None,
    alternative: Optional[str] = None
) -> Callable[[F], F]:
    """Mark function as deprecated."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            message = f"Function {func.__name__} is deprecated"
            
            if version:
                message += f" since version {version}"
            
            if reason:
                message += f": {reason}"
            
            if alternative:
                message += f". Use {alternative} instead"
            
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            logger.warning(message)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_types(**type_hints) -> Callable[[F], F]:
    """Validate function argument types."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # Validate types
            for param_name, expected_type in type_hints.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if value is not None and not isinstance(value, expected_type):
                        raise TypeError(
                            f"Parameter '{param_name}' must be of type {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(cls):
    """Singleton decorator for classes."""
    instances = {}
    lock = threading.Lock()
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def rate_limit(calls: int, period: float) -> Callable[[F], F]:
    """Rate limiting decorator."""
    def decorator(func: F) -> F:
        call_times = []
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            with lock:
                # Remove old calls outside the period
                call_times[:] = [t for t in call_times if current_time - t < period]
                
                # Check if we're at the limit
                if len(call_times) >= calls:
                    sleep_time = period - (current_time - call_times[0])
                    if sleep_time > 0:
                        logger.debug(f"Rate limit reached for {func.__name__}, sleeping {sleep_time:.2f}s")
                        time.sleep(sleep_time)
                        current_time = time.time()
                        call_times[:] = [t for t in call_times if current_time - t < period]
                
                # Record this call
                call_times.append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def exception_handler(
    exception_types: tuple = (Exception,),
    default_return: Any = None,
    log_exceptions: bool = True,
    reraise: bool = False
) -> Callable[[F], F]:
    """Handle exceptions with optional logging and default return."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_exceptions:
                    logger.exception(f"Exception in {func.__name__}: {e}")
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def property_cache(func: F) -> F:
    """Cache property values (for use with @property)."""
    cache_name = f"_cached_{func.__name__}"
    
    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, cache_name):
            setattr(self, cache_name, func(self))
        return getattr(self, cache_name)
    
    # Add method to clear cache
    def clear_cache(self):
        if hasattr(self, cache_name):
            delattr(self, cache_name)
    
    wrapper.clear_cache = clear_cache
    return wrapper