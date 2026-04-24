"""
Public configuration API for ``psychchart``.

This package centralizes the strongly typed configuration models used across
the ``psychchart`` project. The exported classes form the public interface for
configuration loading, validation, normalization, and runtime integration.

The design intentionally exposes a small set of well-defined models rather
than requiring downstream code to import from many internal modules. This
improves readability, reduces coupling, and makes the configuration layer
easier to use from loaders, command-line interfaces, notebooks, and tests.

Architecture
------------
The configuration package is organized by responsibility:

- ``base``:
  strict shared validation behavior
- ``chart``:
  global chart-level configuration
- ``isolines``:
  isoline family definitions
- ``zones``:
  geometric and index-derived zones
- ``points``:
  reference points
- ``indexes``:
  computed index configuration and rendering
- ``observations``:
  legacy observational dataset configuration
- ``overlays``:
  legacy temporal trajectory overlays
- ``data_layers``:
  canonical unified configuration for dataset-driven layers
- ``app``:
  validated root application configuration
- ``paths``:
  ordered trajectory in psychrometric space

Notes
-----
This module is intentionally lightweight. It does not define new models by
itself; instead, it re-exports the public configuration classes so users can
import them from a single, stable location.

Examples
--------
Import the public configuration models from one place:

>>> from psychchart.config import AppConfig, ChartConfig, IsoSet
>>> ChartConfig.__name__
'ChartConfig'

Validate a minimal root configuration:

>>> raw = {
...     "chart": {
...         "t_min": 0.0,
...         "t_max": 50.0,
...         "pressure": 101325.0,
...         "xlabel": "Dry-bulb temperature (°C)",
...         "ylabel": "Humidity ratio (kg/kg)",
...         "output": "chart.png",
...         "dpi": 150,
...     }
... }
>>> cfg = AppConfig.model_validate(raw)
>>> cfg.chart.output
'chart.png'
"""

# -----------------------------------------------------------------------------
# Root application model
# -----------------------------------------------------------------------------
# ``AppConfig`` is the main entry point for validating the full merged
# configuration document used by the runtime.
from .app import AppConfig

# -----------------------------------------------------------------------------
# Global chart configuration
# -----------------------------------------------------------------------------
# ``ChartConfig`` stores domain limits, axis labels, export options, pressure,
# and other chart-wide parameters.
from .chart import ChartConfig

# -----------------------------------------------------------------------------
# Isoline configuration
# -----------------------------------------------------------------------------
# ``IsoSet`` defines a semantic family of isolines, such as relative humidity,
# enthalpy, or other chart overlays represented as contour-like line groups.
from .isolines import IsoSet

# -----------------------------------------------------------------------------
# Zone configuration
# -----------------------------------------------------------------------------
# ``Zone`` represents explicit geometric zones in chart space.
# ``IndexZone`` represents semantic zones derived from scalar index intervals.
from .zones import Zone, IndexZone

# -----------------------------------------------------------------------------
# Point configuration
# -----------------------------------------------------------------------------
# ``Point`` defines a single annotated reference point in psychrometric space.
from .points import Point

# -----------------------------------------------------------------------------
# Index configuration and rendering
# -----------------------------------------------------------------------------
# These classes define both the semantic identity of computed indices and the
# way they can be rendered as continuous fields and/or isolines.
from .indexes import (
    FieldRenderConfig,
    IsolineRenderConfig,
    IndexRenderConfig,
    IndexConfig,
)

# -----------------------------------------------------------------------------
# Observational dataset configuration
# -----------------------------------------------------------------------------
# These classes describe dataset-based visual layers such as density fields and
# data-driven scalar visualizations derived from observational files.
from .observations import (
    DensityFieldConfig,
    DataIndexConfig,
    ObservationsConfig,
)

# -----------------------------------------------------------------------------
# Temporal overlay configuration
# -----------------------------------------------------------------------------
# ``TemporalOverlayConfig`` describes time-ordered trajectories drawn over the
# psychrometric chart.
from .overlays import TemporalOverlayConfig

# -----------------------------------------------------------------------------
# Canonical unified data-layer configuration
# -----------------------------------------------------------------------------
from .data_layers import (
    ProjectionConfig,
    TemporalConfig,
    DirectColumnFieldConfig,
    DataIndexFieldConfig,
    PointsRenderConfig,
    ScatterRenderConfig,
    DensityRenderConfig as DataLayerDensityRenderConfig,
    ScalarFieldRenderConfig,
    PathRenderConfig,
    AnnotateRenderConfig,
    DataLayerConfig,
)

# -----------------------------------------------------------------------------
# Global declarative legend configuration.
# -----------------------------------------------------------------------------
from .legend import (
        LegendPatchEntry,
        LegendLineEntry,
        LegendMarkerEntry,
        LegendConfig,
)

# -----------------------------------------------------------------------------
# Shared strict validation base
# -----------------------------------------------------------------------------
# ``StrictModel`` is the common strict Pydantic base used by the public
# configuration models.
from .base import StrictModel

# -----------------------------------------------------------------------------
# Psychrometric path configuration
# -----------------------------------------------------------------------------
# ``PathConfig`` defines ordered trajectories in psychrometric space, including
# optional scalar values for progressive color mapping.
from .paths import PathConfig


# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
from .operations import (
    OperationalOverlayConfig,
    OperationalProfileConfig,
)
# -----------------------------------------------------------------------------
# Optional explicit public export list
# -----------------------------------------------------------------------------
# Defining ``__all__`` makes the public API explicit and communicates which
# names are intended for external consumption. This is especially useful for
# package users, static analysis tools, and documentation generation.
__all__: list[str] = [
    "AppConfig",
    "ChartConfig",
    "IsoSet",
    "Zone",
    "IndexZone",
    "Point",
    "FieldRenderConfig",
    "IsolineRenderConfig",
    "IndexRenderConfig",
    "IndexConfig",
    "DensityFieldConfig",
    "DataIndexConfig",
    "ObservationsConfig",
    "TemporalOverlayConfig",
    "ProjectionConfig",
    "TemporalConfig",
    "DirectColumnFieldConfig",
    "DataIndexFieldConfig",
    "PointsRenderConfig",
    "ScatterRenderConfig",
    "DataLayerDensityRenderConfig",
    "ScalarFieldRenderConfig",
    "PathRenderConfig",
    "AnnotateRenderConfig",
    "DataLayerConfig",
    "PathConfig",
    "LegendPatchEntry",
    "LegendLineEntry",
    "LegendMarkerEntry",
    "LegendConfig",
    "OperationalOverlayConfig",
    "OperationalProfileConfig",
    "StrictModel",
]
