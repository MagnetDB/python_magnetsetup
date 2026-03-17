# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Make the package importable when building docs without installing it.
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -------------------------------------------------------
project = "python-magnetsetup"
copyright = "2024, Christophe Trophime, Romain Vallet, Jeremie Muzet, Remi Caumette"
author = "Christophe Trophime, Romain Vallet, Jeremie Muzet, Remi Caumette"

try:
    from importlib.metadata import version as _v

    release = _v("python-magnetsetup")
except Exception:
    release = "0.0.0.dev0"

version = ".".join(release.split(".")[:2])

# -- General configuration -----------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # NumPy / Google style docstrings
    "sphinx.ext.viewcode",  # [source] links
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",  # render type hints in docs
    "myst_parser",  # Markdown support (for README, LOGGING.md, …)
]

# autodoc
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}
autodoc_typehints = "description"
autoclass_content = "both"
autosummary_generate = True

# Napoleon
napoleon_google_docstring = False
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True

# intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# MyST
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3  # generate anchors so README ToC links resolve
# Suppress cross-reference warnings for relative links in included Markdown
# files (e.g. README.md → LOGGING.md) that are valid outside Sphinx.
# Also suppress forward-reference warnings from pint's internal annotations.
suppress_warnings = [
    "myst.xref_missing",
    "sphinx_autodoc_typehints.forward_reference",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 4,
    "titles_only": False,
}

# -- Options for todo extension ------------------------------------------------
todo_include_todos = True
