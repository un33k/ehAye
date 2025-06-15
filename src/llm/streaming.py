"""Streaming response handling utilities."""

import time
from typing import Any, Generator, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from ..core.logging import get_logger

logger = get_logger("llm.streaming")


class StreamHandler:
    """Handles streaming text output with rich formatting."""
    
    def __init__(self, enable_markdown: bool = False):
        self.console = Console()
        self.enable_markdown = enable_markdown
        self.current_text = ""
    
    def stream_to_console(
        self, 
        stream: Generator[str, None, None],
        prefix: str = "🤖 Assistant: "
    ) -> str:
        """Stream text to console with real-time updates."""
        self.current_text = ""
        
        # Print prefix
        self.console.print(prefix, end="", style="bold blue")
        
        start_time = time.time()
        
        try:
            for chunk in stream:
                self.current_text += chunk
                self.console.print(chunk, end="", style="white")
                
            # Final newline
            self.console.print()
            
            generation_time = time.time() - start_time
            self._print_stats(generation_time)
            
            return self.current_text
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Generation interrupted[/yellow]")
            return self.current_text
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            self.console.print(f"\n[red]Error: {e}[/red]")
            return self.current_text
    
    def stream_with_live_markdown(
        self, 
        stream: Generator[str, None, None],
        title: str = "Assistant Response"
    ) -> str:
        """Stream with live markdown rendering."""
        self.current_text = ""
        
        with Live(console=self.console, refresh_per_second=4) as live:
            start_time = time.time()
            
            try:
                for chunk in stream:
                    self.current_text += chunk
                    
                    if self.enable_markdown:
                        content = Markdown(self.current_text)
                    else:
                        content = Text(self.current_text)
                    
                    live.update(content)
                
                generation_time = time.time() - start_time
                self._print_stats(generation_time)
                
                return self.current_text
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Generation interrupted[/yellow]")
                return self.current_text
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                self.console.print(f"\n[red]Error: {e}[/red]")
                return self.current_text
    
    def stream_to_callback(
        self, 
        stream: Generator[str, None, None],
        callback: callable,
        **callback_kwargs
    ) -> str:
        """Stream with custom callback function."""
        self.current_text = ""
        
        try:
            for chunk in stream:
                self.current_text += chunk
                callback(chunk, self.current_text, **callback_kwargs)
            
            return self.current_text
            
        except Exception as e:
            logger.error(f"Streaming callback error: {e}")
            return self.current_text
    
    def _print_stats(self, generation_time: float) -> None:
        """Print generation statistics."""
        if not self.current_text:
            return
        
        words = len(self.current_text.split())
        chars = len(self.current_text)
        tokens_estimated = words * 1.3
        
        words_per_sec = words / generation_time if generation_time > 0 else 0
        tokens_per_sec = tokens_estimated / generation_time if generation_time > 0 else 0
        
        self.console.print(
            f"\n[dim]⚡ {words} words, {chars} chars in {generation_time:.2f}s "
            f"({tokens_per_sec:.1f} tokens/sec)[/dim]"
        )


class BufferedStreamHandler:
    """Handles streaming with buffering for smoother output."""
    
    def __init__(self, buffer_size: int = 5, flush_interval: float = 0.1):
        self.console = Console()
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer = []
        self.last_flush = time.time()
    
    def stream_buffered(
        self, 
        stream: Generator[str, None, None],
        prefix: str = "🤖 Assistant: "
    ) -> str:
        """Stream with buffering for smoother output."""
        self.buffer = []
        full_text = ""
        
        # Print prefix
        self.console.print(prefix, end="", style="bold blue")
        
        start_time = time.time()
        
        try:
            for chunk in stream:
                full_text += chunk
                self.buffer.append(chunk)
                
                # Flush buffer if conditions met
                current_time = time.time()
                if (len(self.buffer) >= self.buffer_size or 
                    current_time - self.last_flush >= self.flush_interval):
                    self._flush_buffer()
            
            # Final flush
            self._flush_buffer()
            
            # Final newline and stats
            self.console.print()
            generation_time = time.time() - start_time
            self._print_stats(full_text, generation_time)
            
            return full_text
            
        except KeyboardInterrupt:
            self._flush_buffer()
            self.console.print("\n[yellow]Generation interrupted[/yellow]")
            return full_text
        except Exception as e:
            logger.error(f"Buffered streaming error: {e}")
            self.console.print(f"\n[red]Error: {e}[/red]")
            return full_text
    
    def _flush_buffer(self) -> None:
        """Flush the current buffer to console."""
        if self.buffer:
            text = "".join(self.buffer)
            self.console.print(text, end="", style="white")
            self.buffer = []
            self.last_flush = time.time()
    
    def _print_stats(self, text: str, generation_time: float) -> None:
        """Print generation statistics."""
        words = len(text.split())
        chars = len(text)
        tokens_estimated = words * 1.3
        
        tokens_per_sec = tokens_estimated / generation_time if generation_time > 0 else 0
        
        self.console.print(
            f"\n[dim]⚡ {words} words, {chars} chars in {generation_time:.2f}s "
            f"({tokens_per_sec:.1f} tokens/sec)[/dim]"
        )


# Global handlers
stream_handler = StreamHandler()
buffered_handler = BufferedStreamHandler()


def stream_to_console(
    stream: Generator[str, None, None],
    prefix: str = "🤖 Assistant: ",
    buffered: bool = False
) -> str:
    """Stream text to console."""
    if buffered:
        return buffered_handler.stream_buffered(stream, prefix)
    else:
        return stream_handler.stream_to_console(stream, prefix)


def stream_with_markdown(
    stream: Generator[str, None, None],
    title: str = "Assistant Response"
) -> str:
    """Stream with markdown rendering."""
    markdown_handler = StreamHandler(enable_markdown=True)
    return markdown_handler.stream_with_live_markdown(stream, title)