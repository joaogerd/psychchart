"""
psychchart
==========

A Python package for generating psychrometric charts using a
configurable, YAML-driven workflow.

This package provides a high-level, reproducible interface for
building psychrometric charts commonly used in:

- thermal comfort studies
- bioclimatology
- building physics
- animal and human heat stress analysis
- educational and scientific visualization

The design philosophy emphasizes:
- scientific reproducibility
- declarative configuration (YAML-based)
- separation of concerns (configuration, loading, plotting)
- extensibility for future indices (THI, HLI, UTCI, etc.)

Versioning
----------
This project follows **Semantic Versioning (SemVer)**:

    MAJOR.MINOR.PATCH

- MAJOR: incompatible API changes
- MINOR: backward-compatible functionality
- PATCH: backward-compatible bug fixes

For a detailed explanation of the versioning policy, see:
`VERSIONING.md`

Attributes
----------
__version__ : str
    Current version of the package, following SemVer.

Exports
-------
The following symbols are exposed at the package level for
user convenience:

- ChartConfig
- IsoSet
- Zone
- Point
- PsychChart
- load_chart_config

This allows users to interact with the package using:

>>> import psychchart
>>> chart = psychchart.PsychChart(...)

or

>>> from psychchart import PsychChart, load_chart_config
"""

# =============================================================================
# Package version
# =============================================================================

# NOTE:
# The version string is intentionally defined here to make it accessible
# programmatically (e.g., psychchart.__version__) and by packaging tools.
__version__ = "0.1.0"


# =============================================================================
# Public API imports
# =============================================================================

# Configuration-related classes
# These define the declarative structure of the chart (axes, isopleths, zones).
from .config import ChartConfig, IsoSet, Zone, Point

# Main plotting interface
# This is the high-level object responsible for rendering the psychrometric chart.
from .plot import PsychChart

# YAML loader utility
# Reads a YAML configuration file and returns a validated ChartConfig instance.
from .loader import load_chart_config


# =============================================================================
# Public symbols
# =============================================================================

# __all__ explicitly defines the public API of the package.
# This controls what is imported when users do:
#
# >>> from psychchart import *
#
# and helps tools like linters, IDEs, and documentation generators.
__all__ = [
    "ChartConfig",
    "IsoSet",
    "Zone",
    "Point",
    "PsychChart",
    "load_chart_config",
]


# =============================================================================
# Usage examples (for documentation purposes)
# =============================================================================
#
# Basic usage with a YAML configuration file:
#
# >>> from psychchart import load_chart_config, PsychChart
# >>> cfg = load_chart_config("configs/basic_chart.yml")
# >>> chart = PsychChart(cfg)
# >>> chart.plot()
#
# Programmatic usage (without YAML):
#
# >>> from psychchart import ChartConfig, IsoSet, PsychChart
# >>> cfg = ChartConfig(
# ...     title="Psychrometric Chart",
# ...     temperature_range=(0, 40),
# ...     humidity_ratio_range=(0, 0.030),
# ...     isos=[
# ...         IsoSet(kind="rh", values=[30, 50, 70]),
# ...     ],
# ... )
# >>> chart = PsychChart(cfg)
# >>> chart.plot()
#
# Accessing the package version:
#
# >>> import psychchart
# >>> psychchart.__version__
# '0.1.0'
#

