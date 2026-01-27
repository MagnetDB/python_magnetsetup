"""Top-level package for Python Magnet SetUp."""

__author__ = """Christophe Trophime"""
__email__ = 'christophe.trophime@lncmi.cnrs.fr'
__version__ = '0.1.0'

# Import logging utilities
from .logging_config import setup_logging, get_logger, init_default_logging

# Initialize default logging
init_default_logging()

__all__ = ['setup_logging', 'get_logger']
