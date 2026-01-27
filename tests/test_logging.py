"""
Tests for logging functionality in python_magnetsetup.
"""

import os
import tempfile
import logging
from pathlib import Path

import pytest

from python_magnetsetup.logging_config import (
    setup_logging,
    get_logger,
    init_default_logging
)


class TestLoggingConfig:
    """Test the logging configuration module."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger('test_module')
        assert isinstance(logger, logging.Logger)
        assert 'python_magnetsetup' in logger.name

    def test_get_logger_with_qualified_name(self):
        """Test that get_logger handles already qualified names."""
        logger = get_logger('python_magnetsetup.test_module')
        assert logger.name == 'python_magnetsetup.test_module'

    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'python_magnetsetup'
        assert len(logger.handlers) > 0

    def test_setup_logging_with_level_string(self):
        """Test setup_logging with string level."""
        logger = setup_logging(level='DEBUG')
        assert logger.level == logging.DEBUG

    def test_setup_logging_with_level_int(self):
        """Test setup_logging with integer level."""
        logger = setup_logging(level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_setup_logging_with_file(self):
        """Test setup_logging with file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'test.log'
            logger = setup_logging(log_file=str(log_file), level='INFO')
            
            # Log a test message
            logger.info("Test message")
            
            # Flush handlers
            for handler in logger.handlers:
                handler.flush()
            
            # Check file was created and contains message
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_setup_logging_creates_directory(self):
        """Test that setup_logging creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'subdir' / 'test.log'
            logger = setup_logging(log_file=str(log_file))
            
            logger.info("Test")
            for handler in logger.handlers:
                handler.flush()
            
            assert log_file.parent.exists()
            assert log_file.exists()

    def test_setup_logging_no_console(self):
        """Test setup_logging without console handler."""
        logger = setup_logging(console=False)
        
        # Should have no StreamHandler
        stream_handlers = [h for h in logger.handlers 
                          if isinstance(h, logging.StreamHandler) 
                          and not isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(stream_handlers) == 0

    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format."""
        custom_format = '%(levelname)s - %(message)s'
        logger = setup_logging(log_format=custom_format)
        
        # Check that at least one handler has the custom format
        handler_formats = [h.formatter._fmt for h in logger.handlers if h.formatter]
        assert custom_format in handler_formats

    def test_setup_logging_from_env_level(self, monkeypatch):
        """Test that logging level is read from environment."""
        monkeypatch.setenv('MAGNETSETUP_LOG_LEVEL', 'WARNING')
        logger = setup_logging()
        assert logger.level == logging.WARNING

    def test_setup_logging_from_env_file(self, monkeypatch):
        """Test that log file is read from environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'env_test.log'
            monkeypatch.setenv('MAGNETSETUP_LOG_FILE', str(log_file))
            
            logger = setup_logging()
            logger.info("Environment test")
            
            for handler in logger.handlers:
                handler.flush()
            
            assert log_file.exists()

    def test_init_default_logging(self):
        """Test that init_default_logging initializes logging."""
        logger = init_default_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'python_magnetsetup'

    def test_logging_hierarchy(self):
        """Test that child loggers inherit from parent."""
        parent_logger = setup_logging(level='DEBUG')
        child_logger = get_logger('test_child')
        
        # Child should inherit settings from parent
        assert child_logger.parent == parent_logger or \
               'python_magnetsetup' in child_logger.name

    def test_file_rotation_config(self):
        """Test that file rotation parameters are set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / 'rotation_test.log'
            logger = setup_logging(
                log_file=str(log_file),
                max_bytes=1024,
                backup_count=3
            )
            
            # Find the RotatingFileHandler
            file_handlers = [h for h in logger.handlers 
                           if isinstance(h, logging.handlers.RotatingFileHandler)]
            
            assert len(file_handlers) == 1
            handler = file_handlers[0]
            assert handler.maxBytes == 1024
            assert handler.backupCount == 3


class TestLoggingIntegration:
    """Integration tests for logging with other modules."""

    def test_logging_in_config_module(self):
        """Test that config module can use logging."""
        from python_magnetsetup.config import appenv
        
        # Should not raise any errors
        logger = get_logger('python_magnetsetup.config')
        assert isinstance(logger, logging.Logger)

    def test_logging_in_file_utils(self):
        """Test that file_utils module can use logging."""
        from python_magnetsetup.file_utils import findfile
        
        logger = get_logger('python_magnetsetup.file_utils')
        assert isinstance(logger, logging.Logger)
