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
from typing import Sequence, List, Optional, Tuple, Dict, Any


# =============================================================================
# Chart-level configuration
# =============================================================================
@dataclass
class ChartConfig:
    """
    Definition of global configuration parameters for a psychrometric chart.

    This class describes the **domain**, **physical context**, and
    **rendering-related options** of a psychrometric chart.

    It acts as a top-level, declarative container defining *how the chart
    should exist*, but not *how it is computed or plotted*.

    This model is intentionally lightweight and declarative.
    It does NOT:
    - validate physical consistency (e.g., pressure limits)
    - enforce logical constraints (e.g., t_min < t_max)
    - perform any plotting or numerical computation

    All validation, inference, and rendering logic must be handled
    by higher-level components.

    Parameters
    ----------
    t_min : float, optional
        Minimum dry-bulb temperature displayed on the x-axis (°C).
    t_max : float, optional
        Maximum dry-bulb temperature displayed on the x-axis (°C).
    y_min : float or None, optional
        Lower bound of humidity ratio (kg_vapor / kg_dry_air).
        If None, defaults to zero or is inferred by the plotting engine.
    y_max : float or None, optional
        Upper bound of humidity ratio (kg_vapor / kg_dry_air).
        If None, it may be inferred automatically.
    pressure : float, optional
        Atmospheric pressure (Pa) assumed for psychrometric calculations.
    output : str, optional
        Output filename or path for the rendered chart.
    dpi : int, optional
        Output resolution in dots per inch.
    style : str or None, optional
        Matplotlib style name (e.g., ``"seaborn-v0_8"``, ``"ggplot"``).
        If None, the default Matplotlib style is used.

    Notes
    -----
    - This class is purely descriptive.
    - Any automatic inference (axis limits, scaling, layout)
      must be performed externally.

    Examples
    --------
    >>> cfg = ChartConfig(
    ...     t_min=0,
    ...     t_max=50,
    ...     pressure=101325,
    ...     output="chart.png"
    ... )
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
    Definition of a set of isolines (isopleths) in the psychrometric chart.

    Each ``IsoSet`` represents a **family of curves** associated with a
    single physical variable, such as relative humidity, enthalpy,
    wet-bulb temperature, or vapor pressure.

    This class describes *what isolines should exist*,
    but not *how they are computed or drawn*.

    This model is intentionally lightweight and declarative.
    It does NOT:
    - compute isoline values
    - validate physical units
    - perform interpolation or plotting

    Interpretation of the ``name`` attribute and numerical evaluation
    are delegated to the plotting backend.

    Parameters
    ----------
    name : str
        Identifier of the isoline type
        (e.g., ``"relative_humidity"``, ``"enthalpy"``, ``"wet_bulb"``).
    values : sequence of float, optional
        Numerical values at which isolines should be drawn.
    style : str, optional
        Matplotlib line style (e.g., ``"-"``, ``"--"``, ``":"``).
    color : str or None, optional
        Fixed color for all isolines.
        Ignored if ``cmap`` is provided.
    cmap : str or None, optional
        Matplotlib colormap name used to color isolines
        according to their magnitude.
    enabled : bool, optional
        Whether this isoline set should be rendered.

    Notes
    -----
    - The meaning of ``values`` depends entirely on ``name``.
    - This design allows easy extension to new isoline types
      without modifying the configuration schema.

    Examples
    --------
    >>> rh_isos = IsoSet(
    ...     name="relative_humidity",
    ...     values=[0.3, 0.5, 0.7, 0.9],
    ...     style="--"
    ... )
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
    Definition of a geometric zone in the psychrometric chart.

    A ``Zone`` represents a **spatially explicit region** of the chart,
    typically used to indicate thermal comfort areas, regulatory limits,
    or operational domains.

    Zones are defined directly in thermodynamic space and can be
    constructed either explicitly (polygon vertices) or implicitly
    (temperature and relative humidity ranges).

    This model is intentionally lightweight and declarative.
    It does NOT:
    - compute psychrometric curves
    - convert RH ranges into humidity ratio
    - generate polygons or perform clipping

    All geometric construction is delegated to the plotting layer.

    Parameters
    ----------
    name : str
        Name of the zone, used in legends and annotations.
    vertices : list of [T, RH] pairs or None, optional
        Explicit polygon vertices defining the zone.
    t_range : sequence of float or None, optional
        Temperature interval ``[T_min, T_max]`` (°C).
    rh_range : sequence of float or None, optional
        Relative humidity interval ``[RH_min, RH_max]`` (0–1).
    follow_rh : bool, optional
        If True, zone boundaries follow RH curves.
    edgecolor : str, optional
        Color of the zone boundary.
    facecolor : str or None, optional
        Fill color of the zone.
    linewidth : float, optional
        Line width of the zone boundary.

    Notes
    -----
    - ``Zone`` differs fundamentally from :class:`IndexZone`:
      it is geometric, not diagnostic.
    - Either ``vertices`` or ``t_range``/``rh_range`` should be provided.

    Examples
    --------
    >>> comfort = Zone(
    ...     name="Comfort zone",
    ...     t_range=(18, 26),
    ...     rh_range=(0.4, 0.7),
    ...     facecolor="lightgreen"
    ... )
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

    A ``Point`` marks a specific thermodynamic state, typically
    corresponding to observed, simulated, or design conditions.

    Points are annotated visually but carry no computational logic.

    This model is intentionally lightweight and declarative.
    It does NOT:
    - convert RH to humidity ratio
    - validate thermodynamic consistency
    - control label placement

    Parameters
    ----------
    label : str
        Text label displayed near the point.
    t : float
        Dry-bulb temperature (°C).
    rh : float
        Relative humidity (0–1).
    marker : str, optional
        Matplotlib marker symbol.
    color : str, optional
        Marker and label color.

    Examples
    --------
    >>> p = Point(
    ...     label="Station A",
    ...     t=32,
    ...     rh=0.6,
    ...     color="red"
    ... )
    """

    label: str
    t: float
    rh: float
    marker: str = "o"
    color: str = "k"

# =============================================================================
# Index configuration
# =============================================================================

@dataclass
class IndexConfig:
    """
    Definition of an index configuration for psychrometric charts.

    This class describes how a **bioclimatic or thermal index**
    (e.g., THI, HLI, ITU, UTCI) should be *represented* in the chart,
    typically through isolines, contours, or derived visual elements.

    An ``IndexConfig`` defines *presentation rules* for an index,
    not the index computation itself.

    This model is intentionally lightweight and declarative.
    It does NOT:
    - compute index values
    - validate index names or modes
    - generate isolines or contours
    - perform plotting or interpolation

    All numerical computation and geometric interpretation are
    delegated to higher-level logic (e.g., an index engine or
    plotting backend).

    Parameters
    ----------
    name : str
        Identifier of the index (e.g., ``"THI"``, ``"HLI"``, ``"ITU"``,
        ``"UTCI"``). The semantic meaning and formula associated with
        this name are handled elsewhere.
    parameters : dict
        Dictionary of index-specific parameters required for computation
        (e.g., wind speed, solar radiation, animal category).
        The content and meaning of this dictionary are index-dependent.
    mode : str
        Rendering or representation mode of the index.
        Typical examples include:
        - ``"isolines"``: draw index contours
        - ``"filled"``: filled contours or masked regions
        - ``"both"``: isolines and filled regions
        The exact interpretation depends on the plotting backend.
    levels : list of float or None, optional
        Index values at which isolines or contour boundaries
        should be drawn.
        If None, levels may be inferred automatically.
    style : str, optional
        Matplotlib line style used for index isolines
        (e.g., ``":"``, ``"--"``, ``"-."``).
    color : str or None, optional
        Fixed color used for rendering index isolines.
        Ignored if a colormap is applied by the backend.

    Notes
    -----
    - ``IndexConfig`` complements :class:`IndexZone`:
        * ``IndexConfig`` → *how the index is visualized*
        * ``IndexZone``   → *how index values are classified*
    - Multiple indices can coexist in the same chart,
      each with its own configuration.

    Examples
    --------
    Configure isolines for the Temperature–Humidity Index (THI):

    >>> from psychchart.config import IndexConfig
    >>> thi_cfg = IndexConfig(
    ...     name="THI",
    ...     mode="isolines",
    ...     levels=[60, 65, 70, 75, 80],
    ...     style=":",
    ...     color="black"
    ... )

    Configure filled contours for the Heat Load Index (HLI):

    >>> hli_cfg = IndexConfig(
    ...     name="HLI",
    ...     mode="filled",
    ...     levels=[70, 80, 90, 100],
    ... )
    """

    # Identifier of the thermal or bioclimatic index (e.g., THI, HLI)
    name: str

    # Rendering mode of the index (isolines, filled, both, etc.)
    mode: str

    # Index-specific parameters passed to the computation engine
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Index values used as contour or classification levels
    levels: Optional[List[float]] = None

    # Colormap used for filled rendering
    cmap: Optional[str] = None

    # Line style for index isolines
    style: str = ":"

    # Fixed color used for index rendering
    color: Optional[str] = None

    # Transparency for filled modes
    alpha: float = 0.6
# =============================================================================
# Index-based Zone configuration
# =============================================================================

@dataclass
class IndexZone:
    """
    Definition of an index-based zone in the psychrometric chart.

    This class represents a *derived* or *diagnostic* zone associated
    with a thermal or bioclimatic index (e.g., ITU, HLI, THI, UTCI),
    rather than directly with geometric constraints such as temperature
    and relative humidity ranges.

    An ``IndexZone`` typically maps a **numeric interval of an index**
    to a visual region in the chart, allowing qualitative interpretation
    such as *comfort*, *alert*, or *danger* levels.

    This model is intentionally lightweight and declarative.
    It does NOT:
    - compute the index
    - validate index ranges
    - convert index ranges into polygons

    All interpretation and geometric construction is delegated to
    higher-level logic (e.g., an index integrator or plotting backend).

    Parameters
    ----------
    index : str
        Identifier of the index used to define the zone.
        Examples include ``"THI"``, ``"HLI"``, ``"ITU"``, ``"UTCI"``.
        The semantic meaning and computation of the index are handled
        elsewhere.
    name : str
        Human-readable name of the zone, typically describing
        physiological or thermal meaning (e.g., ``"Comfort"``,
        ``"Heat Stress"``, ``"Severe Stress"``).
    range : tuple of float
        Inclusive numeric interval ``(min_value, max_value)``
        of the index defining this zone.
    color : str
        Base color used to render the zone.
        This should be a valid Matplotlib color specification.
    alpha : float, optional
        Transparency level of the zone fill (0–1).
        Lower values result in more transparent zones.

    Notes
    -----
    - ``IndexZone`` is conceptually different from :class:`Zone`:
      it does not define geometry directly, but rather a **classification
      rule** based on an index.
    - A plotting engine may translate an ``IndexZone`` into:
        * shaded RH-following regions
        * masked areas
        * contour-based fills
    - Multiple ``IndexZone`` objects can be defined for the same index
      to represent different severity levels.

    Examples
    --------
    Define zones based on the Temperature–Humidity Index (THI):

    >>> from psychchart.config import IndexZone
    >>> comfort = IndexZone(
    ...     index="THI",
    ...     name="Comfort",
    ...     range=(0.0, 72.0),
    ...     color="green",
    ...     alpha=0.25
    ... )

    >>> alert = IndexZone(
    ...     index="THI",
    ...     name="Heat stress",
    ...     range=(72.0, 78.0),
    ...     color="orange",
    ...     alpha=0.3
    ... )

    >>> danger = IndexZone(
    ...     index="THI",
    ...     name="Severe heat stress",
    ...     range=(78.0, 100.0),
    ...     color="red",
    ...     alpha=0.35
    ... )

    These zones can later be interpreted by an index-aware plotting
    layer that computes THI over the chart domain and fills the
    corresponding regions.
    """

    # Identifier of the thermal or bioclimatic index (e.g., THI, HLI)
    index: str

    # Descriptive name of the zone (used in legends and annotations)
    name: str

    # Inclusive numeric interval of the index defining the zone
    range: Tuple[float, float]

    # Base color used for visual rendering
    color: str

    # Transparency level of the zone fill
    alpha: float = 0.3

@dataclass
class IndexField:
    """
    Definition of a continuous index field visualization.

    This class describes how a **continuous bioclimatic or thermal index**
    (e.g., ITU, HLI, THI, UTCI) should be rendered as a **scalar field**
    over the psychrometric chart domain.

    An ``IndexField`` represents a *background layer* or *overlay*
    where index values are evaluated on a (T, RH) grid and displayed
    using a colormap.

    This model is intentionally lightweight and declarative.
    It does NOT:
    - compute index values
    - validate index names
    - perform interpolation
    - draw colorbars or contours directly
    - enforce value limits

    All numerical computation and rendering logic are delegated
    to higher-level plotting routines.

    Parameters
    ----------
    index : str
        Identifier of the index to be rendered as a continuous field
        (e.g., ``"ITU"``, ``"HLI"``, ``"THI"``, ``"UTCI"``).
        The computation associated with this identifier is handled
        elsewhere.
    cmap : str, optional
        Name of the Matplotlib colormap used to map index values
        to colors (default is ``"viridis"``).
    levels : int or None, optional
        Number of discrete color levels used to represent the field.
        If None, a continuous colormap is used.
    vmin : float or None, optional
        Lower bound for index values in the colormap normalization.
        If None, the minimum value is inferred automatically.
    vmax : float or None, optional
        Upper bound for index values in the colormap normalization.
        If None, the maximum value is inferred automatically.
    alpha : float, optional
        Transparency level of the field (0–1).
        Lower values allow underlying chart elements to remain visible.
    colorbar : bool, optional
        Whether a colorbar should be drawn for this index field.

    Notes
    -----
    - ``IndexField`` complements:
        * :class:`IndexConfig` → isolines / contours
        * :class:`IndexZone`   → classified regions
    - Only one field per index is typically meaningful,
      but the schema does not enforce this.
    - Color normalization strategy (linear, log, etc.)
      must be handled externally.

    Design considerations
    ---------------------
    - This class is designed for *visual density* representation
      of indices rather than categorical interpretation.
    - Rendering order matters: index fields are usually drawn
      before isolines, zones, and reference points.
    - The class is declarative to support YAML/JSON-driven workflows.

    Examples
    --------
    Render the Heat Load Index (HLI) as a background field:

    >>> from psychchart.config import IndexField
    >>> hli_field = IndexField(
    ...     index="HLI",
    ...     cmap="inferno",
    ...     vmin=60,
    ...     vmax=100,
    ...     alpha=0.5,
    ...     colorbar=True
    ... )

    Render ITU with a fixed number of color levels:

    >>> itu_field = IndexField(
    ...     index="ITU",
    ...     levels=20,
    ...     cmap="plasma",
    ...     alpha=0.6
    ... )
    """

    # Identifier of the thermal or bioclimatic index
    index: str

    # Colormap used for field visualization
    cmap: str = "viridis"

    # Number of discrete color levels (None for continuous)
    levels: Optional[int] = None

    # Lower bound for colormap normalization
    vmin: Optional[float] = None

    # Upper bound for colormap normalization
    vmax: Optional[float] = None

    # Transparency of the field layer
    alpha: float = 0.6

    # Whether a colorbar should be displayed
    colorbar: bool = True


# =============================================================================
# Usage examples
# =============================================================================
#
# Example 1: Programmatic configuration
#
# >>> from psychchart.config import (
# ...     ChartConfig, IsoSet, Zone, Point, IndexConfig, IndexZone
# ... )
#
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
# >>> thi_cfg = IndexConfig(
# ...     name="THI",
# ...     mode="isolines",
# ...     levels=[60, 65, 70, 75, 80],
# ...     style=":",
# ...     color="black"
# ... )
#
# >>> thi_comfort = IndexZone(
# ...     index="THI",
# ...     name="Comfort",
# ...     range=(0.0, 72.0),
# ...     color="green",
# ...     alpha=0.25
# ... )
#
# >>> thi_alert = IndexZone(
# ...     index="THI",
# ...     name="Heat stress",
# ...     range=(72.0, 78.0),
# ...     color="orange",
# ...     alpha=0.3
# ... )
#
# >>> thi_danger = IndexZone(
# ...     index="THI",
# ...     name="Severe heat stress",
# ...     range=(78.0, 100.0),
# ...     color="red",
# ...     alpha=0.35
# ... )
#
# >>> itu_field = IndexField(
# ...     index="ITU",
# ...     levels=20,
# ...     cmap="plasma",
# ...     alpha=0.6
# ... )
#
# =============================================================================
# Example 2: Conceptual YAML-driven workflow
# =============================================================================
#
# This example illustrates how the configuration models can be
# serialized in YAML and later interpreted by a loader or plotting
# engine.
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
#     style: "--"
# 
# zones:
#   - name: Comfort zone
#     t_range: [18, 26]
#     rh_range: [0.4, 0.7]
#     facecolor: lightgreen
#     edgecolor: green
# 
# points:
#   - label: Station A
#     t: 32
#     rh: 0.6
#     marker: o
#     color: red
#
# indexes:
#   - name: ITU
#     mode: isolines
#     levels: [72, 78, 82]
#     style: ":"
#     color: darkred
#
# index_zones:
#   - index: THI
#     name: Comfort
#     range: [0.0, 72.0]
#     color: green
#     alpha: 0.25
# 
#   - index: THI
#     name: Heat stress
#     range: [72.0, 78.0]
#     color: orange
#     alpha: 0.3
# 
#   - index: THI
#     name: Severe heat stress
#     range: [78.0, 100.0]
#     color: red
#     alpha: 0.35
#
# index_fields:
#   - index: ITU
#     cmap: inferno
#     levels: 20
#     alpha: 0.6
#     colorbar: true


