"""
Logging configuration for python_magnetsetup.

This module provides a centralized logging configuration that can be used
throughout the package.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(
    level=None,
    log_file=None,
    log_format=None,
    date_format=None,
    console=True,
    file_mode='a',
    max_bytes=10485760,  # 10MB
    backup_count=5
):
    """
    Set up logging for the application.
    
    Parameters
    ----------
    level : int or str, optional
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        If None, reads from MAGNETSETUP_LOG_LEVEL env var or defaults to INFO.
    log_file : str or Path, optional
        Path to log file. If None, reads from MAGNETSETUP_LOG_FILE env var.
        If still None, only console logging is used.
    log_format : str, optional
        Custom log format string. If None, uses default format.
    date_format : str, optional
        Custom date format string. If None, uses default format.
    console : bool, optional
        Whether to log to console. Default is True.
    file_mode : str, optional
        File mode for log file ('a' for append, 'w' for overwrite). Default is 'a'.
    max_bytes : int, optional
        Maximum size in bytes before rotating log file. Default is 10MB.
    backup_count : int, optional
        Number of backup files to keep. Default is 5.
    
    Returns
    -------
    logging.Logger
        Configured root logger.
    """
    # Get logging level
    if level is None:
        level_str = os.environ.get('MAGNETSETUP_LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, level_str, logging.INFO)
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Get log file from environment if not specified
    if log_file is None:
        log_file = os.environ.get('MAGNETSETUP_LOG_FILE')
    
    # Default formats
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if date_format is None:
        date_format = '%Y-%m-%d %H:%M:%S'
    
    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # Get root logger
    root_logger = logging.getLogger('python_magnetsetup')
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        # Create parent directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent unlimited growth
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            mode=file_mode,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    root_logger.propagate = False
    
    return root_logger


def get_logger(name):
    """
    Get a logger instance for a specific module.
    
    Parameters
    ----------
    name : str
        Name of the logger (typically __name__ of the module).
    
    Returns
    -------
    logging.Logger
        Logger instance.
    """
    # Ensure the logger is a child of python_magnetsetup
    if not name.startswith('python_magnetsetup'):
        name = f'python_magnetsetup.{name}'
    
    return logging.getLogger(name)


# Initialize default logging configuration
_default_logger = None


def init_default_logging():
    """Initialize default logging configuration if not already done."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging()
    return _default_logger
