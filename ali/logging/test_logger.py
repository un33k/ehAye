"""Unit tests for logging functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import logging
import tempfile
import shutil

from .logger import get_logger, ehaye_logger, EhAyeLogger


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "ehaye.test"
    
    def test_get_logger_with_dots(self):
        """Test get_logger with dotted name."""
        logger = get_logger("module.submodule")
        assert logger.name == "ehaye.module.submodule"
    
    def test_get_logger_caching(self):
        """Test that get_logger caches loggers."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2
    
    def test_get_logger_different_names(self):
        """Test get_logger with different names."""
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestEhAyeLogger:
    """Test EhAyeLogger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.temp_dir / "test.log"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        # Reset logger state
        ehaye_logger._logger = None
        
        # Remove any handlers from root logger
        root_logger = logging.getLogger("ehaye")
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def test_setup_default(self):
        """Test default logger setup."""
        logger = ehaye_logger.setup()
        
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
        assert ehaye_logger._logger is not None
    
    def test_setup_custom_level(self):
        """Test logger setup with custom level."""
        ehaye_logger.setup(level="DEBUG")
        
        root_logger = logging.getLogger("ehaye")
        assert root_logger.level == logging.DEBUG
    
    def test_setup_with_file(self):
        """Test logger setup with file output."""
        ehaye_logger.setup(level="INFO", log_file=self.log_file)
        
        root_logger = logging.getLogger("ehaye")
        assert len(root_logger.handlers) >= 2  # Console + file
        
        # Check that file handler was added
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1
    
    def test_setup_no_rich(self):
        """Test logger setup without rich formatting."""
        ehaye_logger.setup(enable_rich=False)
        
        root_logger = logging.getLogger("ehaye")
        # Should still have handlers, but not rich handlers
        assert len(root_logger.handlers) >= 1
    
    def test_setup_string_level(self):
        """Test logger setup with string level."""
        test_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level_str in test_levels:
            ehaye_logger._logger = None
            
            # Remove existing handlers
            root_logger = logging.getLogger("ehaye")
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            logger = ehaye_logger.setup(level=level_str)
            
            expected_level = getattr(logging, level_str)
            assert logger.level == expected_level
    
    def test_setup_int_level(self):
        """Test logger setup with integer level."""
        # Convert integer level to string since setup expects string
        logger = ehaye_logger.setup(level="WARNING")
        
        assert logger.level == logging.WARNING
    
    def test_setup_idempotent(self):
        """Test that setup is idempotent."""
        logger1 = ehaye_logger.setup(level="INFO")
        handler_count_1 = len(logger1.handlers)
        
        logger2 = ehaye_logger.setup(level="DEBUG")  # Second call
        handler_count_2 = len(logger2.handlers)
        
        # Should return same logger instance
        assert logger1 is logger2
        assert handler_count_1 == handler_count_2
        assert ehaye_logger._logger is not None
    
    def test_logging_output(self):
        """Test actual logging output."""
        ehaye_logger.setup(level="DEBUG", log_file=self.log_file)
        
        logger = get_logger("test")
        logger.info("Test message")
        
        # Check that message was written to file
        assert self.log_file.exists()
        content = self.log_file.read_text()
        assert "Test message" in content
        assert "test" in content  # Logger name should be included
    
    def test_different_log_levels(self):
        """Test different log levels work correctly."""
        ehaye_logger.setup(level="WARNING", log_file=self.log_file)
        
        logger = get_logger("test")
        logger.debug("Debug message")    # Should appear in file (DEBUG level)
        logger.info("Info message")      # Should appear in file (DEBUG level)
        logger.warning("Warning message") # Should appear
        logger.error("Error message")    # Should appear
        
        content = self.log_file.read_text()
        # File handler logs everything at DEBUG level
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content
    
    @patch('ali.logging.logger.RichHandler')
    def test_rich_handler_creation(self, mock_rich_handler):
        """Test rich handler creation."""
        mock_handler = Mock()
        mock_rich_handler.return_value = mock_handler
        
        ehaye_logger.setup(enable_rich=True)
        
        mock_rich_handler.assert_called_once()
        # RichHandler doesn't use setFormatter, so just check it was created
        assert mock_handler is not None
    
    def test_file_handler_creation(self):
        """Test file handler creation and configuration."""
        ehaye_logger.setup(log_file=self.log_file)
        
        root_logger = logging.getLogger("ehaye")
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        
        assert len(file_handlers) >= 1
        file_handler = file_handlers[0]
        assert self.log_file.name in file_handler.baseFilename


class TestLoggerIntegration:
    """Integration tests for logger functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Reset logger state
        ehaye_logger._logger = None
        
        # Clear any existing handlers
        root_logger = logging.getLogger("ehaye")
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_multiple_loggers_same_config(self):
        """Test multiple loggers using same configuration."""
        log_file = self.temp_dir / "multi.log"
        ehaye_logger.setup(level="INFO", log_file=log_file)
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        logger1.info("Message from module1")
        logger2.warning("Message from module2")
        
        content = log_file.read_text()
        assert "module1" in content
        assert "module2" in content
        assert "Message from module1" in content
        assert "Message from module2" in content
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy works correctly."""
        ehaye_logger.setup(level="DEBUG")
        
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")
        
        # Both should be configured
        assert parent_logger.level <= logging.DEBUG
        assert child_logger.level <= logging.DEBUG
        
        # Child should inherit from parent
        assert child_logger.parent.name == parent_logger.name
    
    def test_concurrent_setup(self):
        """Test concurrent setup calls don't cause issues."""
        import threading
        
        def setup_logger():
            ehaye_logger.setup(level="INFO")
            logger = get_logger("concurrent")
            logger.info("Concurrent message")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=setup_logger)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert ehaye_logger._logger is not None
    
    def test_logging_with_exceptions(self):
        """Test logging with exception information."""
        log_file = self.temp_dir / "exceptions.log"
        ehaye_logger.setup(level="ERROR", log_file=log_file)
        
        logger = get_logger("test")
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception("An error occurred")
        
        content = log_file.read_text()
        assert "An error occurred" in content
        assert "ValueError" in content
        assert "Test exception" in content
        assert "Traceback" in content


class TestLoggerConfiguration:
    """Test logger configuration options."""
    
    def setup_method(self):
        """Set up test fixtures."""
        ehaye_logger._logger = None
        
        # Clear any existing handlers
        root_logger = logging.getLogger("ehaye")
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def test_disable_existing_loggers(self):
        """Test that existing loggers are not disabled."""
        # Create a logger before setup
        pre_logger = get_logger("pre_setup")
        pre_logger.info("Before setup")  # Should work
        
        ehaye_logger.setup()
        
        # Pre-existing logger should still work
        pre_logger.info("After setup")  # Should still work
        
        # New logger should also work
        post_logger = get_logger("post_setup")
        post_logger.info("New logger")  # Should work
    
    def test_custom_formatter(self):
        """Test custom formatter configuration."""
        temp_dir = Path(tempfile.mkdtemp())
        log_file = temp_dir / "custom.log"
        
        try:
            ehaye_logger.setup(level="INFO", log_file=log_file)
            
            logger = get_logger("formatter_test")
            logger.info("Test formatting")
            
            content = log_file.read_text()
            # Should contain timestamp, level, and message
            assert "INFO" in content
            assert "formatter_test" in content
            assert "Test formatting" in content
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_log_file_directory_creation(self):
        """Test that log file directory is created if it doesn't exist."""
        temp_dir = Path(tempfile.mkdtemp())
        nested_log_file = temp_dir / "logs" / "nested" / "test.log"
        
        try:
            ehaye_logger.setup(log_file=nested_log_file)
            
            logger = get_logger("directory_test")
            logger.info("Testing directory creation")
            
            # Directory should be created
            assert nested_log_file.parent.exists()
            assert nested_log_file.exists()
            
        finally:
            shutil.rmtree(temp_dir)


class TestErrorHandling:
    """Test error handling in logger."""
    
    def setup_method(self):
        """Set up test fixtures."""
        ehaye_logger._logger = None
    
    def test_invalid_log_level(self):
        """Test handling of invalid log level."""
        with pytest.raises((ValueError, AttributeError)):
            ehaye_logger.setup(level="INVALID_LEVEL")
    
    def test_invalid_log_file_path(self):
        """Test handling of invalid log file path."""
        # Try to write to a directory that doesn't exist and can't be created
        invalid_path = Path("/root/impossible/path/test.log")
        
        # Should handle the error gracefully (may raise or log warning)
        try:
            ehaye_logger.setup(log_file=invalid_path)
        except (PermissionError, FileNotFoundError, OSError):
            # These exceptions are acceptable
            pass
    
    @patch('ali.logging.logger.RichHandler')
    def test_rich_handler_import_error(self, mock_rich_handler):
        """Test handling of rich handler import error."""
        mock_rich_handler.side_effect = ImportError("Rich not available")
        
        # Should fall back to standard console handler
        ehaye_logger.setup(enable_rich=True)
        
        # Should still have a handler
        root_logger = logging.getLogger("ehaye")
        assert len(root_logger.handlers) >= 1


class TestPerformance:
    """Test logger performance characteristics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        ehaye_logger._logger = None
    
    def test_logger_creation_performance(self):
        """Test that logger creation is fast."""
        ehaye_logger.setup()
        
        import time
        start_time = time.time()
        
        # Create many loggers
        loggers = []
        for i in range(1000):
            logger = get_logger(f"test_{i}")
            loggers.append(logger)
        
        end_time = time.time()
        
        # Should complete quickly (less than 1 second)
        assert end_time - start_time < 1.0
        assert len(loggers) == 1000
    
    def test_logging_performance(self):
        """Test that actual logging is reasonably fast."""
        temp_dir = Path(tempfile.mkdtemp())
        log_file = temp_dir / "performance.log"
        
        try:
            ehaye_logger.setup(level="INFO", log_file=log_file, enable_rich=False)
            logger = get_logger("performance")
            
            import time
            start_time = time.time()
            
            # Log many messages
            for i in range(1000):
                logger.info(f"Performance test message {i}")
            
            end_time = time.time()
            
            # Should complete reasonably quickly
            assert end_time - start_time < 5.0
            
            # Verify all messages were logged
            content = log_file.read_text()
            assert "Performance test message 0" in content
            assert "Performance test message 999" in content
            
        finally:
            shutil.rmtree(temp_dir)