# Setup and Run Magnet Simulation

This package contains the tools to generate files required for the setup of magnet simulation
along with the commands that need to be run to actually perform the simulation.

This package is called from the magnetdb web interface or from the cli python_magnetapi
to perform the setup.

To use the cli mode, please refer to python_magnetapi doc.

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installation Methods](#installation-methods)
  - [Development Installation](#development-installation)
- [Usage](#usage)
  - [Main Functionality](#main-functionality)
  - [Configuration Files](#configuration-files)
  - [Templates](#templates)
- [Logging](#logging)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python >= 3.5 (recommended: Python 3.11+)
- `python_magnetgeo` package (required dependency)
- Access to magnetdb web interface or python_magnetapi CLI

### Installation Methods

#### Using pip

```bash
pip install -r requirements.txt
pip install .
```

#### Using Poetry (recommended)

```bash
poetry install
```

#### Using setup.py

```bash
python setup.py install
```

### Development Installation

For development work, install with dev dependencies:

```bash
# Using pip
pip install -r requirements_dev.txt
pip install -e .

# Using Poetry
poetry install --with dev
```

#### Dependencies

Core dependencies:
- `python_magnetgeo` - Geometry handling for magnets
- `fabric` >= 2.7.0 - Remote execution and deployment
- `Pint` >= 0.18 - Physical units handling
- `python-decouple` >= 3.6 - Configuration management
- `requests` >= 2.27.1 - HTTP library
- `chevron` >= 0.13.1 - Mustache templating
- `PyYAML` >= 6.0 - YAML parsing

Development dependencies:
- `pytest` >= 4.6.5 - Testing framework
- `flake8` - Code linting
- `Sphinx` - Documentation generation
- `coverage` - Code coverage
- `tox` - Testing automation

## Usage

### Command Line Usage

The package provides command-line interfaces for common operations:

#### Creating Simulation Templates (ana.py)

Generate template JSON model files for Feelpp/HiFiMagnet simulations:

```bash
# Using a data file
python -m python_magnetsetup.ana --datafile HL-34-data.json

# With working directory
python -m python_magnetsetup.ana --datafile HL-34-data.json --wd /path/to/workdir

# With debug output
python -m python_magnetsetup.ana --datafile HL-34-data.json --debug --verbose

# From magnetdb (magnet name)
python -m python_magnetsetup.ana --magnet HL-34

# From magnetdb (site name)
python -m python_magnetsetup.ana --msite HL-31
```

**Options:**
- `--datafile FILE` - Input data file (e.g., HL-34-data.json)
- `--wd DIR` - Set working directory
- `--magnet NAME` - Magnet name from magnetdb (e.g., HL-34)
- `--msite NAME` - MSite name from magnetdb (e.g., HL-31)
- `--debug` - Activate debug mode
- `--verbose` - Activate verbose output

**Note:** `--magnet` and `--msite` are mutually exclusive. Cannot specify both `--datafile` and `--magnet`/`--msite`.

#### Converting Units (units.py)

Change units according to specified length unit:

```bash
# Convert to meters (default)
python -m python_magnetsetup.units --datafile HL-34-data.json

# Convert to millimeters
python -m python_magnetsetup.units --datafile HL-34-data.json --length_unit millimeter

# With working directory
python -m python_magnetsetup.units --datafile HL-34-data.json --wd /path/to/workdir --debug

# From magnetdb
python -m python_magnetsetup.units --magnet HL-34 --length_unit meter
```

**Options:**
- `--datafile FILE` - Input data file (e.g., HL-34-data.json)
- `--wd DIR` - Set working directory
- `--magnet NAME` - Magnet name from magnetdb (e.g., HL-34)
- `--length_unit {meter,millimeter}` - Length unit (default: meter)
- `--debug` - Activate debug mode

#### Using Makefile Commands

Common development tasks can be performed using make:

```bash
# Install the package
make install

# Run tests
make test

# Run tests with coverage
make coverage

# Run tests on all Python versions
make test-all

# Check code style
make lint

# Clean build artifacts
make clean

# Build distribution packages
make dist

# Generate documentation
make docs

# Serve documentation with auto-reload
make servedocs

# Release to PyPI
make release
```

#### Data Archiving

Archive simulation data (excluding generated files):

```bash
# Archive all data
./archive-data.sh

# Creates magnetdb-data.tgz excluding:
# - CAD files (*.xao, *.brep)
# - Mesh files (*.med, *.msh, *.stl)
# - Log files (*.log)
# - Temporary files (*~, #*#)
# - Python compiled files (*.pyc)
# - HDF5 files (*.h5, *.hdf)
```

### Main Functionality

The package provides tools for setting up magnet simulations with different configurations:

#### Creating Simulation Files

The main module `python_magnetsetup.setup` provides functions to create simulation files:

```python
from python_magnetsetup.setup import magnet_setup, magnet_simfile
from python_magnetgeo.Insert import Insert

# Load your configuration
confdata = {
    'geom': 'path/to/geometry.yaml',
    'method': 'cfpdes',  # or 'getdp'
    'time': 'stationary',  # or 'transient'
    'geom_type': 'Axi',  # or '3D'
    'model': 'thmag',  # thermomagnetism
    # ... other parameters
}

# Create simulation files
cad = Insert(...)  # Load your CAD model
files = magnet_simfile(MyEnv, confdata, cad, addAir=False)
```

#### Supported Simulation Types

- **Methods**: `cfpdes`, `getdp`, `CG`
- **Time modes**: `stationary`, `transient`
- **Geometries**: `Axi` (axisymmetric), `3D`
- **Physical models**:
  - `thelec` - Thermoelectric
  - `thmag` - Thermomagnetism
  - `thmagel` - Thermomagnetism with elasticity
  - `thmqs` - Thermomagnetism quasi-static
  - `mqs` - Magnetoquasistatic
  - `mag` - Magnetism
  - `*_hcurl` - H-curl formulations

### Configuration Files

The package uses several configuration files:

- **`magnetsetup.json`** - Main setup configuration defining mustache templates
- **`machines.json`** - Machine/cluster specifications
- **`flow_params.json`** - Flow parameters for simulations
- **`settings.env`** - Environment settings
- **YAML files** - Geometry and material definitions (stored in `data/geometries/`)

### Templates

Mustache templates are organized by:
- Solver method (`cfpdes`, `CG`)
- Geometry type (`Axi`, `3D`)
- Physical model (`thelec`, `thmag`, `thmagel`, etc.)

Templates are located in `python_magnetsetup/templates/`.

### Working with Different Magnet Types

#### Insert Magnets

```python
from python_magnetsetup.insert import Insert_setup, Insert_simfile

# Setup and create simulation files for insert magnets
Insert_setup(MyEnv, confdata, cad)
files = Insert_simfile(MyEnv, confdata, cad, addAir=False)
```

#### Bitter Magnets

```python
from python_magnetsetup.bitter import Bitter_setup

# Setup for Bitter magnets
Bitter_setup(MyEnv, confdata, cad)
```

#### Superconducting Magnets

```python
from python_magnetsetup.supra import Supra_setup, Supra_simfile

# Setup and create simulation files for superconducting magnets
Supra_setup(MyEnv, confdata, cad)
files = Supra_simfile(MyEnv, confdata, cad)
```

### Utilities

The package provides several utility modules:

- **`units.py`** - Unit conversion and handling
- **`file_utils.py`** - File operations with path searching
- **`cfg.py`** - CFG file generation
- **`jsonmodel.py`** - JSON model creation
- **`node.py`** - Node specification for clusters
- **`job.py`** - Job manager integration

### Example Workflow

#### Command Line Workflow

```bash
# 1. Create a working directory
mkdir -p ~/magnet_simulations/HL-34
cd ~/magnet_simulations/HL-34

# 2. Prepare your data file (e.g., HL-34-data.json)
# This file should contain geometry, materials, and simulation parameters

# 3. Generate simulation templates
python -m python_magnetsetup.ana --datafile HL-34-data.json --verbose

# 4. (Optional) Convert units if needed
python -m python_magnetsetup.units --datafile HL-34-data.json --length_unit millimeter

# 5. Check generated files
ls -la
# Should see configuration files, JSON models, and CFG files
```

#### Python API Workflow

```python
from python_magnetsetup.config import loadconfig, loadtemplates
from python_magnetsetup.setup import magnet_setup
from python_magnetgeo.Insert import Insert

# 1. Load configuration
config = loadconfig('path/to/config.json')
templates = loadtemplates('path/to/magnetsetup.json')

# 2. Load geometry
cad = Insert('path/to/geometry.yaml')

# 3. Setup simulation
confdata = {
    'geom': 'geometry.yaml',
    'method': 'cfpdes',
    'time': 'stationary',
    'geom_type': 'Axi',
    'model': 'thmag',
    'phytype': 'linear',
    'cooling': 'mean'
}

# 4. Generate setup files
magnet_setup(MyEnv, confdata, cad)
```

#### Complete Example with Multiple Magnets

```bash
# For a Bitter magnet configuration
python -m python_magnetsetup.ana \
    --datafile Bitter_M10_BE-data.json \
    --wd /data/simulations/Bitter_M10 \
    --verbose

# For an insert with multiple components
python -m python_magnetsetup.ana \
    --datafile HL-31_H1-data.json \
    --wd /data/simulations/HL-31 \
    --debug
```

## Logging

The package includes comprehensive logging support for debugging and monitoring. See [LOGGING.md](LOGGING.md) for detailed documentation.

### Quick Start

Logging is automatically initialized when importing the package:

```python
import python_magnetsetup
from python_magnetsetup.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Starting simulation setup")
```

### Configuration

Control logging via environment variables:

```bash
export MAGNETSETUP_LOG_LEVEL=DEBUG
export MAGNETSETUP_LOG_FILE=/var/log/magnetsetup.log
```

Or programmatically:

```python
from python_magnetsetup import setup_logging

setup_logging(level='DEBUG', log_file='simulation.log')
```

For more details, see [LOGGING.md](LOGGING.md).

## Project Structure

```
python_magnetsetup/
├── __init__.py           # Package initialization
├── setup.py             # Main setup module
├── config.py            # Configuration handling
├── cfg.py               # CFG file generation
├── jsonmodel.py         # JSON model creation
├── insert.py            # Insert magnet setup
├── bitter.py            # Bitter magnet setup
├── supra.py             # Superconducting magnet setup
├── ana.py               # Analysis tools
├── job.py               # Job manager
├── node.py              # Node specifications
├── units.py             # Unit handling
├── utils.py             # General utilities
├── file_utils.py        # File utilities
├── objects.py           # Object loading
├── flatten.py           # Data flattening
├── templates/           # Mustache templates
│   ├── cfpdes/
│   │   ├── Axi/
│   │   └── 3D/
│   └── CG/
└── postprocessing/      # Post-processing tools
```

## Debian Packaging

The package includes Debian packaging files for creating `.deb` packages suitable for Debian and Ubuntu systems.

### Package Information

- **Source Package**: `python-magnetsetup`
- **Binary Packages**:
  - `python3-magnetsetup` - Main Python 3 library
  - `python-magnetsetup-doc` - Documentation package
- **Maintainer**: Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
- **Homepage**: https://github.com/Trophime/python_magnetsetup

### Building Debian Package

#### Prerequisites

Install build dependencies:

```bash
sudo apt-get install debhelper-compat dh-python python3-setuptools python3-all \
                     python3-gmsh python3-yaml python3-lxml python3-pytest-runner
```

#### Build the debian Package

```bash
./archive.sh -d trixie -v 0.1.0 # Replace 'trixie' with your Debian/Ubuntu codename
```

The built packages will be created in the parent directory:
- `python3-magnetsetup_<version>_all.deb` - Main package
- `python-magnetsetup-doc_<version>_all.deb` - Documentation package

#### Install the Debian Package

```bash
# Install the main package
sudo dpkg -i ../python3-magnetsetup_*.deb

# Install dependencies if needed
sudo apt-get install -f

# Install documentation package (optional)
sudo dpkg -i ../python-magnetsetup-doc_*.deb
```

### Package Dependencies

**Build Dependencies:**
- `debhelper-compat (= 12)`
- `dh-python`
- `python3-setuptools`
- `python3-all`
- `python3-gmsh`
- `python3-yaml`
- `python3-lxml`
- `python3-pytest-runner`

**Runtime Dependencies:**
- `python3-decouple`
- `python3-chevron`
- `python3-requests`
- `python3-magnettools`

### Debian Packaging Files

The `debian/` directory contains:

- **`control`** - Package metadata and dependencies
- **`rules`** - Build rules using `dh` and `pybuild`
- **`changelog`** - Version history and changes
- **`copyright`** - License and copyright information
- **`python-magnetsetup-docs.docs`** - Documentation files to include
- **`watch`** - Upstream version tracking
- **`patches/`** - Debian-specific patches
- **`source/`** - Source format specification

### Updating the Package

To create a new Debian package version:

```bash
# Update the changelog
dch -i

# Edit the changelog with your changes, then build
dpkg-buildpackage -us -uc -b
```

### Standards Compliance

- **Standards-Version**: 4.6.0
- **Rules-Requires-Root**: no
- Follows Debian Python Policy

### Notes

- The package uses `pybuild` build system for Python 3 compatibility
- Tests are currently disabled in the build process (see `debian/rules`)
- Documentation building is available but commented out in rules file

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Install development dependencies (`pip install -r requirements_dev.txt`)
4. Make your changes
5. Run tests (`pytest`)
6. Check code quality (`flake8`)
7. Commit your changes (`git commit -am 'Add feature'`)
8. Push to the branch (`git push origin feature/your-feature`)
9. Create a Pull Request

## License

MIT License - See LICENSE file for details

## Authors

- Christophe Trophime <christophe.trophime@lncmi.cnrs.fr>
- Romain Vallet <romain.vallet@lncmi.cnrs.fr>
- Jeremie Muzet <jeremie.muzet@lncmi.cnrs.fr>
- Remi Caumette <remicaumette@icloud.com>

## Related Projects

- `python_magnetgeo` - Geometry handling for magnet simulations
- `python_magnetapi` - CLI interface for magnet simulations
- MagnetDB - Web interface for magnet database and simulations
