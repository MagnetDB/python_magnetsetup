#!/usr/bin/env python
"""
Example script demonstrating logging usage in python_magnetsetup.

This script shows different ways to configure and use logging.
"""

from python_magnetsetup import setup_logging, get_logger
from python_magnetsetup.config import appenv

# Example 1: Using default logging (already initialized)
logger = get_logger(__name__)
logger.info("Example 1: Using default logging configuration")

# Example 2: Customizing log level
print("\n--- Example 2: Setting DEBUG level ---")
setup_logging(level='DEBUG')
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")

# Example 3: Logging to file
print("\n--- Example 3: Logging to file ---")
setup_logging(
    level='INFO',
    log_file='/tmp/magnetsetup_example.log',
    console=True
)
logger.info("This message goes to both console and file")
logger.debug("This debug message won't appear (level is INFO)")
print("Check /tmp/magnetsetup_example.log for the log file")

# Example 4: Using logging with actual module functionality
print("\n--- Example 4: Logging in appenv module ---")
setup_logging(level='DEBUG')

try:
    # This will try to load settings.env and log debug information
    env = appenv(debug=True)
    logger.info(f"Environment initialized: URL_API={env.url_api}")
except Exception as e:
    logger.error(f"Error initializing environment: {e}", exc_info=True)

# Example 5: Different log levels
print("\n--- Example 5: Demonstrating all log levels ---")
logger.debug("DEBUG: Detailed diagnostic information")
logger.info("INFO: General informational messages")
logger.warning("WARNING: Something unexpected happened")
logger.error("ERROR: A serious problem occurred")
logger.critical("CRITICAL: A very serious error")

# Example 6: Logging with context
print("\n--- Example 6: Logging with context ---")
def process_magnet(magnet_name):
    """Example function with logging."""
    logger.info(f"Processing magnet: {magnet_name}")
    try:
        # Simulate some processing
        result = {"name": magnet_name, "status": "processed"}
        logger.debug(f"Processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to process magnet {magnet_name}: {e}", exc_info=True)
        raise

result = process_magnet("HL-34")
logger.info(f"Magnet processing complete: {result}")

print("\n--- Examples complete ---")
print("Logging has been demonstrated successfully!")
