"""
Zone configuration models for psychchart.

This module defines typed configuration models for geometric and semantic
regions drawn on psychrometric charts.

Zones may be defined explicitly through vertices or implicitly through
temperature and relative-humidity intervals. They can represent comfort
regions, experimental envelopes, warning bands, management regions, and other
bioclimatic overlays.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field, field_validator

from .base import StrictModel
from .utils import normalize_rh


class Zone(StrictModel):
    """
    Definition of a geometric zone on the chart.

    A zone describes a region in psychrometric space. The user may define the
    region with explicit vertices in ``(T, RH)`` space or with a rectangular
    ``t_range``/``rh_range`` envelope. When ``follow_rh`` is true, the lower
    and upper humidity boundaries follow relative-humidity curves after
    conversion to humidity ratio.

    The optional label fields are intended for bioclimatic overlays, where the
    figure must identify regions directly inside the chart instead of relying
    only on external legends.

    Parameters
    ----------
    name : str
        Semantic identifier and default legend label.
    vertices : list of list of float, optional
        Explicit polygon vertices in ``(T, RH)`` coordinates.
    t_range : tuple of float, optional
        Dry-bulb temperature range in degrees Celsius.
    rh_range : tuple of float, optional
        Relative humidity range. Values may be fractions or percentages and are
        normalized internally to fractions in ``[0, 1]``.
    follow_rh : bool, default=False
        If true, interval-based zones are bounded by RH curves.
    edgecolor : str, default="k"
        Boundary color.
    facecolor : str, optional
        Fill color. Use ``none`` or omit it for an unfilled zone.
    linewidth : float, default=1.5
        Boundary width.
    alpha : float, default=0.3
        Fill opacity. Also used as a soft default for visual overlays.
    label : str, optional
        Text drawn inside or near the zone. If omitted, ``name`` is used when
        ``show_label`` is true.
    show_label : bool, default=False
        Whether to draw a text label for the zone.
    label_t : float, optional
        Explicit label temperature coordinate. If omitted, the polygon centroid
        is used.
    label_rh : float, optional
        Explicit label relative-humidity coordinate. Requires ``label_t`` to be
        useful. Values may be fractions or percentages.
    label_color : str, optional
        Text color. Defaults to ``edgecolor`` when omitted.
    label_fontsize : int, default=9
        Label font size.
    label_rotation : float, default=0.0
        Label rotation in degrees.
    label_bbox : dict, optional
        Matplotlib-compatible annotation bounding-box dictionary.
    """

    name: str
    vertices: Optional[List[List[float]]] = None
    t_range: Optional[Tuple[float, float]] = None
    rh_range: Optional[Tuple[float, float]] = None
    follow_rh: bool = False

    edgecolor: str = "k"
    facecolor: Optional[str] = None
    linewidth: float = 1.5
    alpha: float = 0.3

    label: Optional[str] = None
    show_label: bool = False
    label_t: Optional[float] = None
    label_rh: Optional[float] = None
    label_color: Optional[str] = None
    label_fontsize: int = 9
    label_rotation: float = 0.0
    label_bbox: Optional[Dict[str, Any]] = None

    @field_validator("rh_range", mode="before")
    @classmethod
    def validate_rh_range(cls, value: Any) -> tuple[float, float] | None:
        """Normalize ``rh_range`` to fractional relative humidity."""
        if value is None:
            return value
        return tuple(normalize_rh(v) for v in value)

    @field_validator("label_rh", mode="before")
    @classmethod
    def validate_label_rh(cls, value: Any) -> float | None:
        """Normalize optional label relative humidity to fraction."""
        if value is None:
            return value
        return normalize_rh(value)


class IndexZone(StrictModel):
    """
    Definition of a semantic zone derived from an index range.

    This model describes regions obtained from intervals of a computed scalar
    index such as ITU, THI, HLI, or another registered indicator.
    """

    index: str
    name: str
    range: Tuple[float, float]
    color: str = "gray"
    alpha: float = 0.3
    parameters: Dict[str, Any] = Field(default_factory=dict)
