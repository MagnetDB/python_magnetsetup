# Logging Support Added to python_magnetsetup

## Summary

Comprehensive logging support has been added to the python_magnetsetup package. This includes:

## Files Created

### 1. Core Logging Module
- **python_magnetsetup/logging_config.py**
  - `setup_logging()` - Configure logging with file and console output
  - `get_logger()` - Get logger instances for modules
  - `init_default_logging()` - Initialize default logging
  - Support for log rotation, custom formats, and environment variables

### 2. Documentation
- **LOGGING.md** - Comprehensive logging guide with examples
- **examples/logging_example.py** - Demonstration script showing various logging features

### 3. Tests
- **tests/test_logging.py** - Complete test suite for logging functionality

## Files Modified

### 1. Package Initialization
- **python_magnetsetup/__init__.py**
  - Imports logging utilities
  - Automatically initializes default logging
  - Exports `setup_logging` and `get_logger` functions

### 2. Example Module Updates
- **python_magnetsetup/config.py**
  - Added logger import and initialization
  - Replaced all `print()` statements with appropriate logging calls
  - Uses `logger.debug()` for debug information

- **python_magnetsetup/file_utils.py**
  - Added logger import and initialization
  - Replaced `print()` with `logger.debug()`
  - Improved import organization

### 3. Documentation
- **README.md**
  - Added "Logging" section in table of contents
  - Added comprehensive logging section with quick start guide
  - Links to detailed LOGGING.md documentation

## Features

### Environment Variables
- `MAGNETSETUP_LOG_LEVEL` - Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MAGNETSETUP_LOG_FILE` - Set log file path

### Log Rotation
- Automatic log rotation at 10MB (configurable)
- Keeps 5 backup files (configurable)

### Flexible Configuration
- Console and/or file logging
- Custom log formats
- Custom date formats
- Multiple log levels
- Child logger hierarchy

### Usage Examples

#### Basic Usage
```python
from python_magnetsetup.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Starting simulation")
```

#### Custom Configuration
```python
from python_magnetsetup import setup_logging

setup_logging(
    level='DEBUG',
    log_file='/path/to/app.log',
    console=True
)
```

#### Environment Variables
```bash
export MAGNETSETUP_LOG_LEVEL=DEBUG
export MAGNETSETUP_LOG_FILE=/var/log/magnetsetup.log
python your_script.py
```

## Testing

Run the test suite:
```bash
pytest tests/test_logging.py -v
```

Run the example script:
```bash
python examples/logging_example.py
```

## Next Steps

To fully integrate logging across the project, you can:

1. Add logging to remaining modules (ana.py, bitter.py, supra.py, etc.)
2. Replace remaining `print()` statements with appropriate logging calls
3. Add logging to error handling paths
4. Configure logging in your application entry points
5. Set up log aggregation for production environments

## Benefits

- **Debugging**: Easier troubleshooting with detailed debug logs
- **Monitoring**: Track application behavior in production
- **Auditing**: Record important events and operations
- **Performance**: Optional file logging doesn't impact console output
- **Flexibility**: Configure logging per environment without code changes
