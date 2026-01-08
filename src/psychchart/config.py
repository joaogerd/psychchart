"""
Configuration models for psychrometric charts.

This module defines lightweight data models (dataclasses)
used to describe the structure and content of a psychrometric
chart, including:

- chart domain and global settings
- sets of isolines (isopleths)
- comfort or stress zones
- reference points

These classes are **pure data containers**:
they do NOT implement parsing, validation, numerical
computations, or plotting logic.

Their main purpose is to:
- provide a clear, typed configuration schema
- support YAML/JSON-driven workflows
- decouple configuration from computation and visualization
"""

from dataclasses import dataclass, field
from typing import Sequence, List, Optional


# =============================================================================
# Chart-level configuration
# =============================================================================
@dataclass
class ChartConfig:
    """
    Global configuration parameters for a psychrometric chart.

    This class defines the domain of the chart, physical constants
    relevant to psychrometric calculations, and output/rendering
    options.

    Parameters
    ----------
    t_min : float, optional
        Minimum dry-bulb temperature shown on the x-axis (°C).
    t_max : float, optional
        Maximum dry-bulb temperature shown on the x-axis (°C).
    y_min : float or None, optional
        Lower bound of humidity ratio (kg_vapor / kg_dry_air).
        If None, defaults to 0.
    y_max : float or None, optional
        Upper bound of humidity ratio (kg_vapor / kg_dry_air).
        If None, it may be inferred automatically during plotting.
    pressure : float, optional
        Atmospheric pressure (Pa) used in psychrometric calculations.
    output : str, optional
        Output file path or filename for the rendered chart.
    dpi : int, optional
        Output resolution (dots per inch).
    style : str or None, optional
        Matplotlib style name (e.g., ``"seaborn-v0_8"``, ``"ggplot"``).
        If None, the default Matplotlib style is used.

    Notes
    -----
    This class does not enforce physical or logical validation.
    Validation (e.g., t_min < t_max) must be handled elsewhere.
    """

    t_min: float = 0.0
    t_max: float = 50.0
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    pressure: float = 101_325.0
    output: str = "chart.png"
    dpi: int = 150
    style: Optional[str] = None


# =============================================================================
# Isoline (isopleth) configuration
# =============================================================================
@dataclass
class IsoSet:
    """
    Definition of a set of isolines (isopleths) to be drawn.

    Each instance represents a family of isolines of the same
    physical quantity (e.g., relative humidity, enthalpy,
    wet-bulb temperature).

    Parameters
    ----------
    name : str
        Identifier of the isoline type (e.g., ``"relative_humidity"``,
        ``"enthalpy"``, ``"wet_bulb"``).
    values : sequence of float, optional
        Values at which isolines should be drawn.
    style : str, optional
        Matplotlib line style (e.g., ``"-"``, ``"--"``, ``":"``).
    color : str or None, optional
        Fixed color for all isolines. Ignored if ``cmap`` is provided.
    cmap : str or None, optional
        Matplotlib colormap name used to color isolines
        according to their magnitude.
    enabled : bool, optional
        Whether this set of isolines should be rendered.

    Notes
    -----
    The semantic meaning of ``name`` is interpreted by the plotting
    logic, not by this class.
    """

    name: str
    values: Sequence[float] = field(default_factory=list)
    style: str = "-"
    color: Optional[str] = None
    cmap: Optional[str] = None
    enabled: bool = True


# =============================================================================
# Zone configuration
# =============================================================================
@dataclass
class Zone:
    """
    Definition of a highlighted region (zone) in the chart.

    Zones can represent thermal comfort regions, heat stress
    thresholds, or any custom domain of interest.

    A zone may be defined in one of two ways:
    - explicitly, via polygon vertices
    - implicitly, via temperature and relative humidity ranges

    Parameters
    ----------
    name : str
        Name of the zone, used in legends and annotations.
    vertices : list of [T, RH] pairs or None, optional
        Explicit polygon vertices defining the zone.
    t_range : sequence of float or None, optional
        Temperature range ``[T_min, T_max]`` (°C) for rectangular
        or RH-following zones.
    rh_range : sequence of float or None, optional
        Relative humidity range ``[RH_min, RH_max]`` (0–1).
    follow_rh : bool, optional
        If True, the zone polygon follows RH curves between
        ``t_range`` bounds.
    edgecolor : str, optional
        Edge (border) color of the zone.
    facecolor : str or None, optional
        Fill color of the zone. Use ``None`` or ``"none"`` for transparency.
    linewidth : float, optional
        Line width of the zone boundary (points).

    Notes
    -----
    Interpretation and conversion to geometric primitives
    is handled entirely by the plotting layer.
    """

    name: str
    vertices: Optional[List[List[float]]] = None
    t_range: Optional[Sequence[float]] = None
    rh_range: Optional[Sequence[float]] = None
    follow_rh: bool = False
    edgecolor: str = "k"
    facecolor: Optional[str] = None
    linewidth: float = 1.5


# =============================================================================
# Reference point configuration
# =============================================================================
@dataclass
class Point:
    """
    Definition of a reference point in the psychrometric chart.

    Points are typically used to mark observed or design
    conditions and are annotated with a textual label.

    Parameters
    ----------
    label : str
        Text label displayed near the point.
    t : float
        Dry-bulb temperature of the point (°C).
    rh : float
        Relative humidity of the point (0–1).
    marker : str, optional
        Matplotlib marker symbol (e.g., ``"o"``, ``"s"``, ``"^"``).
    color : str, optional
        Color of the marker and label text.
    """

    label: str
    t: float
    rh: float
    marker: str = "o"
    color: str = "k"

# =============================================================================
# Usage examples
# =============================================================================
#
# Example 1: Programmatic configuration
#
# >>> from psychchart.config import ChartConfig, IsoSet, Zone, Point
# >>> cfg = ChartConfig(
# ...     t_min=5,
# ...     t_max=40,
# ...     output="psychchart.png",
# ...     style="seaborn-v0_8"
# ... )
#
# >>> rh_isos = IsoSet(
# ...     name="relative_humidity",
# ...     values=[0.3, 0.5, 0.7, 0.9],
# ...     style="--"
# ... )
#
# >>> comfort_zone = Zone(
# ...     name="Thermal comfort",
# ...     t_range=(18, 26),
# ...     rh_range=(0.4, 0.7),
# ...     facecolor="lightgreen",
# ...     edgecolor="green"
# ... )
#
# >>> ref_point = Point(
# ...     label="Observed condition",
# ...     t=30,
# ...     rh=0.65,
# ...     marker="o",
# ...     color="red"
# ... )
#
#
# Example 2: Conceptual YAML-driven workflow
#
# chart:
#   t_min: 0
#   t_max: 50
#   pressure: 101325
#   output: chart.png
#
# isos:
#   - name: relative_humidity
#     values: [0.3, 0.5, 0.7, 0.9]
#
# zones:
#   - name: Comfort zone
#     t_range: [18, 26]
#     rh_range: [0.4, 0.7]
#
# points:
#   - label: Station A
#     t: 32
#     rh: 0.6
#

