"""Async utilities and helpers."""

import asyncio
import functools
import time
from typing import Any, Awaitable, Callable, List, Optional, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor

from ..exceptions import EhAyeError
from ..logging import get_logger

logger = get_logger("utilities.async")

T = TypeVar('T')


def run_async(coro: Awaitable[T]) -> T:
    """Run an async coroutine in a synchronous context."""
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an event loop, we can't use asyncio.run()
        # This is a limitation when mixing sync/async code
        raise RuntimeError("Cannot run async code from within an event loop")
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(coro)


async def gather_tasks(
    tasks: List[Awaitable[T]],
    return_exceptions: bool = False,
    timeout: Optional[float] = None
) -> List[Union[T, Exception]]:
    """Gather multiple async tasks with optional timeout."""
    if not tasks:
        return []
    
    try:
        if timeout:
            return await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=return_exceptions),
                timeout=timeout
            )
        else:
            return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    
    except asyncio.TimeoutError:
        # Cancel remaining tasks
        for task in tasks:
            if hasattr(task, 'cancel'):
                task.cancel()
        raise


async def async_retry(
    coro_func: Callable[..., Awaitable[T]],
    *args,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> T:
    """Async retry with exponential backoff."""
    attempt = 1
    current_delay = delay
    
    while attempt <= max_attempts:
        try:
            return await coro_func(*args, **kwargs)
        except exceptions as e:
            if attempt == max_attempts:
                logger.error(f"Async function failed after {max_attempts} attempts: {e}")
                raise
            
            logger.debug(f"Async attempt {attempt} failed: {e}")
            
            await asyncio.sleep(current_delay)
            current_delay *= backoff
            attempt += 1
    
    raise RuntimeError("Should never reach here")  # Type checker satisfaction


async def async_timeout(
    coro: Awaitable[T],
    timeout_seconds: float,
    timeout_message: Optional[str] = None
) -> T:
    """Add timeout to an async operation."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        message = timeout_message or f"Operation timed out after {timeout_seconds} seconds"
        raise EhAyeError(message)


async def run_in_thread(
    func: Callable[..., T],
    *args,
    executor: Optional[ThreadPoolExecutor] = None,
    **kwargs
) -> T:
    """Run a synchronous function in a thread pool."""
    loop = asyncio.get_running_loop()
    
    if executor is None:
        # Create a default executor
        executor = ThreadPoolExecutor(max_workers=4)
    
    # Use functools.partial to pass arguments
    partial_func = functools.partial(func, *args, **kwargs)
    
    try:
        return await loop.run_in_executor(executor, partial_func)
    except Exception as e:
        logger.error(f"Error running {func.__name__} in thread: {e}")
        raise


class AsyncRateLimiter:
    """Async rate limiter."""
    
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.call_times = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit permission."""
        current_time = time.time()
        
        async with self._lock:
            # Remove old calls
            self.call_times = [t for t in self.call_times if current_time - t < self.period]
            
            # Check if we need to wait
            if len(self.call_times) >= self.calls:
                sleep_time = self.period - (current_time - self.call_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    current_time = time.time()
                    self.call_times = [t for t in self.call_times if current_time - t < self.period]
            
            # Record this call
            self.call_times.append(current_time)


class AsyncCache:
    """Simple async cache implementation."""
    
    def __init__(self, ttl: Optional[float] = None, max_size: int = 128):
        self.ttl = ttl
        self.max_size = max_size
        self._cache = {}
        self._timestamps = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if self.ttl is not None:
                if time.time() - self._timestamps[key] > self.ttl:
                    del self._cache[key]
                    del self._timestamps[key]
                    return None
            
            return self._cache[key]
    
    async def set(self, key: str, value: Any):
        """Set value in cache."""
        async with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    async def clear(self):
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()


async def async_map(
    func: Callable[[T], Awaitable[Any]],
    items: List[T],
    concurrency: int = 10
) -> List[Any]:
    """Apply async function to list of items with concurrency limit."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def bounded_func(item):
        async with semaphore:
            return await func(item)
    
    tasks = [bounded_func(item) for item in items]
    return await asyncio.gather(*tasks)


async def async_filter(
    predicate: Callable[[T], Awaitable[bool]],
    items: List[T],
    concurrency: int = 10
) -> List[T]:
    """Filter list using async predicate with concurrency limit."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def bounded_predicate(item):
        async with semaphore:
            return await predicate(item)
    
    results = await asyncio.gather(*[bounded_predicate(item) for item in items])
    return [item for item, keep in zip(items, results) if keep]


class AsyncContextManager:
    """Base class for async context managers."""
    
    async def __aenter__(self):
        """Enter async context."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.cleanup()
    
    async def setup(self):
        """Setup resources (override in subclass)."""
        pass
    
    async def cleanup(self):
        """Cleanup resources (override in subclass)."""
        pass


class AsyncQueue:
    """Async queue with additional features."""
    
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._finished = asyncio.Event()
        self._workers = []
    
    async def put(self, item: Any):
        """Put item in queue."""
        await self._queue.put(item)
    
    async def get(self) -> Any:
        """Get item from queue."""
        return await self._queue.get()
    
    def task_done(self):
        """Mark task as done."""
        self._queue.task_done()
    
    async def join(self):
        """Wait for all tasks to complete."""
        await self._queue.join()
    
    async def process_with_workers(
        self,
        worker_func: Callable[[Any], Awaitable[None]],
        num_workers: int = 5
    ):
        """Process queue items with multiple workers."""
        async def worker():
            while not self._finished.is_set():
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    await worker_func(item)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Worker error: {e}")
                    self._queue.task_done()
        
        # Start workers
        self._workers = [asyncio.create_task(worker()) for _ in range(num_workers)]
        
        # Wait for queue to be empty
        await self._queue.join()
        
        # Signal workers to stop
        self._finished.set()
        
        # Wait for workers to complete
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        # Reset for next use
        self._finished.clear()
        self._workers.clear()


def async_lru_cache(maxsize: int = 128, ttl: Optional[float] = None):
    """LRU cache decorator for async functions."""
    def decorator(func):
        cache = AsyncCache(ttl=ttl, max_size=maxsize)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = str(hash((args, tuple(sorted(kwargs.items())))))
            
            # Try to get from cache
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator