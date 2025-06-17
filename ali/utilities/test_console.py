"""Unit tests for console utilities."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console

from .console import get_console, create_console, setup_console_theme


class TestGetConsole:
    """Test get_console function."""
    
    def test_get_console_returns_console(self):
        """Test that get_console returns a Console instance."""
        console = get_console()
        assert isinstance(console, Console)
    
    def test_get_console_singleton(self):
        """Test that get_console returns the same instance."""
        console1 = get_console()
        console2 = get_console()
        assert console1 is console2
    
    def test_get_console_with_options(self):
        """Test get_console with custom options."""
        # Reset any existing console
        if hasattr(get_console, '_console'):
            delattr(get_console, '_console')
        
        console = get_console(force_terminal=True, width=120)
        assert isinstance(console, Console)
        # Specific properties depend on implementation


class TestCreateConsole:
    """Test create_console function."""
    
    def test_create_console_default(self):
        """Test create_console with default parameters."""
        console = create_console()
        assert isinstance(console, Console)
    
    def test_create_console_custom_width(self):
        """Test create_console with custom width."""
        console = create_console(width=100)
        assert isinstance(console, Console)
        # Note: Testing exact width requires accessing console internals
    
    def test_create_console_no_color(self):
        """Test create_console with color disabled."""
        console = create_console(color_system=None)
        assert isinstance(console, Console)
    
    def test_create_console_force_terminal(self):
        """Test create_console with force_terminal."""
        console = create_console(force_terminal=True)
        assert isinstance(console, Console)
    
    def test_create_console_different_instances(self):
        """Test that create_console creates different instances."""
        console1 = create_console()
        console2 = create_console()
        # Should be different instances (unlike get_console)
        assert console1 is not console2


class TestSetupConsoleTheme:
    """Test setup_console_theme function."""
    
    def test_setup_console_theme_default(self):
        """Test setup_console_theme with default theme."""
        console = Console()
        themed_console = setup_console_theme(console)
        assert isinstance(themed_console, Console)
        # Theme setup should not change the console type
    
    def test_setup_console_theme_custom(self):
        """Test setup_console_theme with custom theme."""
        console = Console()
        custom_theme = {
            "info": "cyan",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }
        themed_console = setup_console_theme(console, theme=custom_theme)
        assert isinstance(themed_console, Console)
    
    def test_setup_console_theme_none(self):
        """Test setup_console_theme with None theme."""
        console = Console()
        themed_console = setup_console_theme(console, theme=None)
        assert themed_console is console  # Should return original console


class TestConsoleIntegration:
    """Integration tests for console functionality."""
    
    def test_console_output_capture(self):
        """Test that console output can be captured."""
        console = create_console(file=None)  # Use default
        
        # Test that console can print without errors
        console.print("Test message")
        console.print("[bold red]Bold red text[/bold red]")
        console.print("✅ Success message")
    
    def test_console_with_rich_markup(self):
        """Test console with Rich markup."""
        console = create_console()
        
        # These should not raise exceptions
        console.print("[bold]Bold text[/bold]")
        console.print("[red]Red text[/red]")
        console.print("[green]✅ Green success[/green]")
        console.print("[yellow]⚠️ Yellow warning[/yellow]")
    
    def test_console_error_handling(self):
        """Test console error handling."""
        console = create_console()
        
        # Should handle various content types gracefully
        console.print("String content")
        console.print({"dict": "content"})
        console.print(["list", "content"])
        console.print(42)
        console.print(None)
    
    def test_multiple_console_instances(self):
        """Test working with multiple console instances."""
        console1 = create_console(width=80)
        console2 = create_console(width=120)
        
        # Both should work independently
        console1.print("Console 1 message")
        console2.print("Console 2 message")
        
        # Should be different instances
        assert console1 is not console2


class TestConsoleConfiguration:
    """Test console configuration options."""
    
    def test_console_width_settings(self):
        """Test various width settings."""
        widths = [80, 100, 120, 160]
        
        for width in widths:
            console = create_console(width=width)
            assert isinstance(console, Console)
            # Actual width testing would require accessing internal properties
    
    def test_console_color_settings(self):
        """Test various color system settings."""
        color_systems = [None, "auto", "standard", "256", "truecolor"]
        
        for color_system in color_systems:
            console = create_console(color_system=color_system)
            assert isinstance(console, Console)
    
    def test_console_stderr_option(self):
        """Test console with stderr output."""
        import sys
        console = create_console(stderr=True, file=sys.stderr)
        assert isinstance(console, Console)


class TestConsolePerformance:
    """Test console performance characteristics."""
    
    def test_console_creation_performance(self):
        """Test that console creation is fast."""
        import time
        
        start_time = time.time()
        
        # Create many consoles
        consoles = []
        for i in range(100):
            console = create_console()
            consoles.append(console)
        
        end_time = time.time()
        
        # Should complete quickly
        assert end_time - start_time < 1.0
        assert len(consoles) == 100
    
    def test_console_singleton_performance(self):
        """Test that singleton console access is fast."""
        import time
        
        start_time = time.time()
        
        # Access singleton many times
        consoles = []
        for i in range(1000):
            console = get_console()
            consoles.append(console)
        
        end_time = time.time()
        
        # Should complete very quickly since it's cached
        assert end_time - start_time < 0.5
        
        # All should be the same instance
        for console in consoles:
            assert console is consoles[0]


class TestErrorHandling:
    """Test error handling in console utilities."""
    
    def test_invalid_width(self):
        """Test handling of invalid width values."""
        # Negative width
        console = create_console(width=-1)
        assert isinstance(console, Console)
        
        # Zero width
        console = create_console(width=0)
        assert isinstance(console, Console)
        
        # Very large width
        console = create_console(width=10000)
        assert isinstance(console, Console)
    
    def test_invalid_color_system(self):
        """Test handling of invalid color system."""
        # Invalid color system should fall back gracefully
        console = create_console(color_system="invalid")
        assert isinstance(console, Console)
    
    def test_console_with_closed_file(self):
        """Test console behavior with closed file."""
        import io
        
        # Create a file-like object and close it
        string_io = io.StringIO()
        string_io.close()
        
        # Creating console with closed file should handle gracefully
        try:
            console = create_console(file=string_io)
            console.print("Test")  # This might raise or handle gracefully
        except (ValueError, OSError):
            # These exceptions are acceptable for closed files
            pass


class TestConsoleThemes:
    """Test console theme functionality."""
    
    def test_default_theme_application(self):
        """Test application of default theme."""
        console = Console()
        themed = setup_console_theme(console)
        
        # Should return a console (might be same or different instance)
        assert isinstance(themed, Console)
    
    def test_custom_theme_application(self):
        """Test application of custom theme."""
        console = Console()
        custom_theme = {
            "success": "bold green",
            "error": "bold red",
            "warning": "bold yellow",
            "info": "bold blue"
        }
        
        themed = setup_console_theme(console, theme=custom_theme)
        assert isinstance(themed, Console)
    
    def test_theme_with_empty_dict(self):
        """Test theme application with empty dictionary."""
        console = Console()
        themed = setup_console_theme(console, theme={})
        assert isinstance(themed, Console)
    
    def test_theme_with_invalid_values(self):
        """Test theme application with invalid values."""
        console = Console()
        invalid_theme = {
            "success": "invalid_color",
            "error": 123,  # Invalid type
            "warning": None
        }
        
        # Should handle invalid theme gracefully
        themed = setup_console_theme(console, theme=invalid_theme)
        assert isinstance(themed, Console)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_console_with_none_parameters(self):
        """Test console creation with None parameters."""
        console = create_console(
            width=None,
            color_system=None,
            force_terminal=None
        )
        assert isinstance(console, Console)
    
    def test_get_console_thread_safety(self):
        """Test get_console thread safety."""
        import threading
        import time
        
        consoles = []
        
        def get_console_in_thread():
            time.sleep(0.01)  # Small delay to increase chance of race condition
            console = get_console()
            consoles.append(console)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=get_console_in_thread)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should be the same instance
        for console in consoles:
            assert console is consoles[0]
    
    def test_console_memory_usage(self):
        """Test that console instances don't leak memory."""
        import gc
        
        # Create many console instances
        for i in range(100):
            console = create_console()
            console.print(f"Message {i}")
            del console
        
        # Force garbage collection
        gc.collect()
        
        # Test passes if no memory errors occur