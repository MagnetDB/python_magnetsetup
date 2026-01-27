# Logging Guide for python_magnetsetup

This document explains how to use the logging functionality in the `python_magnetsetup` package.

## Quick Start

The logging is automatically initialized when you import the package:

```python
import python_magnetsetup
```

## Using Logging in Your Code

### In Package Modules

To use logging in any module within the package:

```python
from python_magnetsetup.logging_config import get_logger

logger = get_logger(__name__)

# Use the logger
logger.debug("Debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

### Configuring Logging

You can customize logging behavior using the `setup_logging()` function:

```python
from python_magnetsetup import setup_logging

# Basic setup with custom level
setup_logging(level='DEBUG')

# Setup with file logging
setup_logging(
    level='INFO',
    log_file='/path/to/logfile.log'
)

# Advanced setup
setup_logging(
    level='DEBUG',
    log_file='/path/to/logfile.log',
    log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    console=True,  # Also log to console
    max_bytes=10485760,  # 10MB max file size
    backup_count=5  # Keep 5 backup files
)
```

## Environment Variables

You can control logging through environment variables:

- `MAGNETSETUP_LOG_LEVEL`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MAGNETSETUP_LOG_FILE`: Path to the log file

Example:

```bash
export MAGNETSETUP_LOG_LEVEL=DEBUG
export MAGNETSETUP_LOG_FILE=/var/log/magnetsetup.log
python your_script.py
```

## Logging Levels

- **DEBUG**: Detailed information, typically of interest only when diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: An indication that something unexpected happened, or indicative of some problem
- **ERROR**: Due to a more serious problem, the software has not been able to perform some function
- **CRITICAL**: A serious error, indicating that the program itself may be unable to continue running

## Log File Rotation

The logging system automatically rotates log files when they reach 10MB (by default). It keeps 5 backup files by default. You can customize these values:

```python
setup_logging(
    log_file='myapp.log',
    max_bytes=5242880,  # 5MB
    backup_count=3  # Keep 3 backups
)
```

## Example Usage

```python
import python_magnetsetup
from python_magnetsetup.logging_config import get_logger

# Get a logger for your module
logger = get_logger(__name__)

def process_data(data):
    logger.info("Starting data processing")
    try:
        # Your code here
        result = do_something(data)
        logger.debug(f"Processing result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing data: {e}", exc_info=True)
        raise
```

## Best Practices

1. **Use appropriate log levels**: Don't log everything as ERROR or INFO
2. **Include context**: Add relevant information to your log messages
3. **Use f-strings**: For better readability and performance
4. **Don't log sensitive data**: Avoid logging passwords, API keys, etc.
5. **Use exc_info=True**: When logging exceptions to include traceback
6. **Get logger per module**: Use `get_logger(__name__)` in each module

## Disabling Console Output

If you only want file logging:

```python
setup_logging(
    log_file='myapp.log',
    console=False
)
```

## Troubleshooting

### Logs not appearing

1. Check the log level - DEBUG messages won't appear if level is set to INFO
2. Verify the log file path exists and is writable
3. Check environment variables aren't overriding your settings

### Duplicate log messages

This usually happens if you call `setup_logging()` multiple times. The function clears existing handlers, but call it only once at the start of your application.
