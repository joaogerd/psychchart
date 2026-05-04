"""
Public configuration API for ``psychchart``.

This package centralizes the strongly typed configuration models used across
the ``psychchart`` project. The exported classes form the public interface for
configuration loading, validation, normalization, and runtime integration.
"""

from .app import AppConfig
from .chart import ChartConfig
from .isolines import IsoSet
from .zones import Zone, IndexZone
from .points import Point
from .indexes import (
    FieldRenderConfig,
    IsolineRenderConfig,
    IndexRenderConfig,
    IndexConfig,
)
from .observations import (
    DensityFieldConfig,
    DataIndexConfig,
    ObservationsConfig,
)
from .overlays import TemporalOverlayConfig
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
from .legend import (
    LegendPatchEntry,
    LegendLineEntry,
    LegendMarkerEntry,
    LegendConfig,
)
from .base import StrictModel
from .paths import PathConfig
from .operations import (
    OperationalOverlayConfig,
    OperationalProfileConfig,
)
from .intervention_zones import (
    ComfortReferenceConfig,
    InterventionConditionConfig,
    InterventionLabelConfig,
    InterventionVectorStyleConfig,
    InterventionRuleConfig,
    InterventionZonesConfig,
)

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
    "ComfortReferenceConfig",
    "InterventionConditionConfig",
    "InterventionLabelConfig",
    "InterventionVectorStyleConfig",
    "InterventionRuleConfig",
    "InterventionZonesConfig",
    "StrictModel",
]
