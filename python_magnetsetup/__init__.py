"""Top-level package for Python Magnet SetUp."""

from importlib.metadata import version, PackageNotFoundError

__author__ = """Christophe Trophime"""
__email__ = "christophe.trophime@lncmi.cnrs.fr"

try:
    __version__ = version("python-magnetsetup")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "0.0.0.dev0"

# Import logging utilities
from .logging_config import setup_logging, get_logger, init_default_logging

# Initialize default logging
init_default_logging()

__all__ = ["setup_logging", "get_logger"]
