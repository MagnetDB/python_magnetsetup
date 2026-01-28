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

    
import python_magnetgeo

MIN_MAGNETGEO_VERSION = "1.0.0"
MAX_MAGNETGEO_VERSION = "2.0.0"

def check_magnetgeo_compatibility():
    """Verify python_magnetgeo version compatibility."""
    try:
        from packaging import version
        current = version.parse(python_magnetgeo.__version__)
        min_ver = version.parse(MIN_MAGNETGEO_VERSION)
        max_ver = version.parse(MAX_MAGNETGEO_VERSION)
        
        if not (min_ver <= current < max_ver):
            raise RuntimeError(
                f"python_magnetsetup requires python_magnetgeo >={MIN_MAGNETGEO_VERSION},<{MAX_MAGNETGEO_VERSION} "
                f"but found {python_magnetgeo.__version__}"
            )
    except ImportError:
        # packaging not available, do basic string check
        if not hasattr(python_magnetgeo, '__version__'):
            raise RuntimeError("python_magnetgeo version cannot be determined")

# Call on import
check_magnetgeo_compatibility()

# Initialize default logging
init_default_logging()

__all__ = ["setup_logging", "get_logger"]
