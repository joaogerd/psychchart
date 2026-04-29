"""
Index configuration models for psychchart.

This module defines typed configuration models used to describe computed
psychrometric or thermal indexes.

Index configuration is split into semantic settings (``levels``, ``colors`` and
``labels``) and rendering settings (field opacity, colorbar visibility and
isoline style). This lets packaged profiles provide defaults while allowing a
user YAML file to override the semantic representation without changing Python
code.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import StrictModel


class FieldRenderConfig(StrictModel):
    """Rendering options for a continuous index field."""

    alpha: Optional[float] = None
    colorbar: Optional[bool] = None


class IsolineRenderConfig(StrictModel):
    """Rendering options for index isolines."""

    levels: Optional[List[float]] = None
    style: Optional[str] = None
    color: Optional[str] = None
    linewidth: Optional[float] = None
    alpha: Optional[float] = None
    label: Optional[bool] = None
    label_fontsize: Optional[int] = None
    label_fmt: Optional[str] = None


class IndexRenderConfig(StrictModel):
    """Composite rendering configuration for an index."""

    field: Optional[FieldRenderConfig] = None
    isolines: Optional[IsolineRenderConfig] = None


class IndexConfig(BaseModel):
    """
    Configuration of a computed thermal or bioclimatic index.

    Recommended YAML shape::

        indexes:
          - index: ITU
            levels: [50, 63, 75, 79]
            colors: ["#1a9850", "#fee08b", "#fdae61"]
            labels: ["Comfort", "Alert", "Stress"]
            render:
              field:
                alpha: 0.65
                colorbar: true

    ``levels``, ``colors`` and ``labels`` are index semantics. They do not live
    under ``render.field``.
    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        populate_by_name=True,
    )

    index: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    levels: Optional[List[float]] = None
    colors: Optional[List[str]] = None
    labels: Optional[List[str]] = None

    cmap: Optional[str] = None
    vmin: Optional[float] = None
    vmax: Optional[float] = None

    render: Optional[IndexRenderConfig] = None

    @model_validator(mode="after")
    def normalize(self) -> "IndexConfig":
        """Normalize legacy aliases after validation."""
        if not self.index and self.name:
            self.index = self.name

        if not self.index:
            raise ValueError(
                "Each index entry must define 'index' or legacy 'name'"
            )

        return self
