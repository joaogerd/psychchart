"""
Plotting engine for psychrometric charts.

This module receives validated configuration objects and
produces a Matplotlib-based psychrometric diagram.

Responsibilities
----------------
- Transform psychrometric relationships into visual elements
- Draw saturation curves, isolines, zones, and reference points
- Handle axis scaling, labels, legends, and styles

Non-responsibilities
--------------------
- YAML parsing
- Input validation
- Command-line interfaces

All inputs are assumed to be **validated and normalized**
before reaching this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Dict, Any, List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .psychrometrics import Psychrometrics
from .config import ChartConfig, IsoSet, Zone, Point, IndexConfig, IndexZone


# =============================================================================
# Internal helper functions
# =============================================================================
def _zone_polygon_rh(zone: Zone, pressure: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate polygon vertices following relative humidity curves.

    This internal helper function constructs a **closed polygon**
    representing a zone bounded by **relative humidity curves**
    between two dry-bulb temperature limits.

    The polygon is defined in thermodynamic space and follows:
    - a lower relative humidity boundary (RH_min)
    - an upper relative humidity boundary (RH_max)
    - closing back to the initial temperature point

    The resulting polygon can be directly used for:
    - filled regions (``ax.fill`` / ``ax.fill_between``)
    - patches (``matplotlib.patches.Polygon``)
    - clipping masks or overlays

    This function is intentionally geometric and low-level.
    It does NOT:
    - validate the zone definition
    - check for physical consistency (e.g., RH bounds)
    - perform plotting
    - handle coordinate transformations

    All validation and rendering must be handled by the caller.

    Parameters
    ----------
    zone : Zone
        Zone object defining the region.
        It must provide:
        - ``t_range = (T_min, T_max)``
        - ``rh_range = (RH_min, RH_max)``
        Relative humidity values are expected as fractions (0–1).
    pressure : float
        Total air pressure (Pa) used in psychrometric conversions.

    Returns
    -------
    T_poly : numpy.ndarray
        One-dimensional array of dry-bulb temperature coordinates (°C)
        defining the polygon vertices.
    W_poly : numpy.ndarray
        One-dimensional array of humidity ratio coordinates
        (kg_vapor / kg_dry_air) defining the polygon vertices.

    Notes
    -----
    - The polygon is constructed in a **clockwise orientation**:
        * lower RH boundary → forward direction
        * upper RH boundary → reverse direction
    - The polygon is explicitly closed by repeating the first point.
    - Humidity ratio is computed using
      :meth:`Psychrometrics.humidity_ratio`.

    Design considerations
    ---------------------
    - The number of sampling points (200) is fixed and chosen
      as a balance between smoothness and performance.
    - The function operates strictly in (T, RH) space
      and converts RH to humidity ratio internally.
    - This function is private (prefixed with ``_``) to allow
      refactoring without breaking the public API.

    Examples
    --------
    Typical internal usage when rendering RH-following zones:

    >>> zone = Zone(
    ...     name="Comfort zone",
    ...     t_range=(18, 26),
    ...     rh_range=(0.4, 0.7),
    ...     follow_rh=True
    ... )
    >>> T_poly, W_poly = _zone_polygon_rh(zone, pressure=101325)
    >>> ax.fill(T_poly, W_poly, facecolor="lightgreen", alpha=0.3)

    The caller is responsible for:
    - checking that ``zone.follow_rh`` is True
    - applying clipping against saturation if needed
    - managing z-order and legend entries
    """

    # ------------------------------------------------------------------
    # Unpack zone limits
    # ------------------------------------------------------------------
    t_lo, t_hi = zone.t_range
    rh_lo, rh_hi = zone.rh_range

    # ------------------------------------------------------------------
    # Lower RH boundary (forward direction)
    # ------------------------------------------------------------------
    # Temperature increases from T_min to T_max
    t_fwd = np.linspace(t_lo, t_hi, 200)

    # Convert lower RH curve to humidity ratio
    w_lo = Psychrometrics.humidity_ratio(t_fwd, rh_lo, pressure)

    # ------------------------------------------------------------------
    # Upper RH boundary (reverse direction)
    # ------------------------------------------------------------------
    # Reverse temperature direction to ensure a closed polygon
    t_rev = t_fwd[::-1]

    # Convert upper RH curve to humidity ratio
    w_hi = Psychrometrics.humidity_ratio(t_rev, rh_hi, pressure)

    # ------------------------------------------------------------------
    # Close polygon
    # ------------------------------------------------------------------
    # Concatenate forward and reverse boundaries and explicitly
    # close the polygon by repeating the initial point.
    T_poly = np.concatenate([t_fwd, t_rev, [t_lo]])
    W_poly = np.concatenate([w_lo, w_hi, [w_lo[0]]])

    return T_poly, W_poly


def _draw_isoline(
    ax: Axes,
    key: str,
    iso: IsoSet,
    t: np.ndarray,
    cfg: ChartConfig
) -> None:
    """
    Draw isolines of a given psychrometric physical quantity.

    This internal helper function is responsible for rendering
    **classical psychrometric isolines** (isopleths) on the chart,
    such as relative humidity, wet-bulb temperature, enthalpy,
    specific volume, and moisture quantity.

    The function operates directly in thermodynamic space and
    draws isolines by evaluating analytical psychrometric
    relationships along the dry-bulb temperature axis.

    This function is intentionally imperative and low-level.
    It does NOT:
    - validate isoline values
    - infer isoline levels automatically
    - manage legends or annotations
    - perform axis scaling or layout
    - convert configuration semantics

    All orchestration, validation, and ordering must be handled
    by the caller.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes where the isolines will be drawn.
    key : str
        Identifier of the physical quantity whose isolines
        should be drawn. Supported values are:
        - ``"relative_humidity"``
        - ``"wet_bulb"``
        - ``"enthalpy"``
        - ``"specific_volume"``
        - ``"moisture_quantity"``
    iso : IsoSet
        Configuration object describing isoline values,
        line style, color, and colormap.
    t : numpy.ndarray
        One-dimensional array of dry-bulb temperatures (°C)
        defining the x-axis sampling of the chart.
    cfg : ChartConfig
        Global chart configuration, providing domain limits
        and atmospheric pressure.

    Notes
    -----
    - All isolines are clipped below the saturation curve.
    - Relative humidity is treated as a fraction (0–1),
      not percentage.
    - This function assumes standard psychrometric constants
      defined in :class:`Psychrometrics`.

    Design considerations
    ---------------------
    - The function is intentionally key-dispatched instead of
      polymorphic to keep scientific logic explicit.
    - Each isoline type is implemented with its canonical
      analytical formulation.
    - The function is private (prefixed with ``_``) to allow
      future refactoring without breaking the public API.

    Examples
    --------
    Typical internal usage:

    >>> t = np.linspace(cfg.t_min, cfg.t_max, 300)
    >>> iso = IsoSet(
    ...     name="relative_humidity",
    ...     values=[0.3, 0.5, 0.7],
    ...     style="--",
    ...     color="gray"
    ... )
    >>> _draw_isoline(ax, "relative_humidity", iso, t, cfg)

    The caller is responsible for:
    - invoking this function in the correct drawing order
    - combining isolines with zones, points, and indices
    - managing legend entries
    """

    # ------------------------------------------------------------------
    # Saturation curve (upper physical limit for humidity ratio)
    # ------------------------------------------------------------------
    # Used to mask isolines so that no line is drawn above saturation.
    w_sat = Psychrometrics.humidity_ratio(t, np.ones_like(t), cfg.pressure)

    # ------------------------------------------------------------------
    # Relative humidity isolines (RH = constant)
    # ------------------------------------------------------------------
    if key == "relative_humidity":
        for rh in iso.values:
            # Color selection:
            # - use colormap if provided
            # - otherwise use fixed color or fallback to black
            color = (
                plt.get_cmap(iso.cmap)(rh) if iso.cmap
                else iso.color or "k"
            )

            # Convert RH to humidity ratio along the temperature axis
            w = Psychrometrics.humidity_ratio(t, rh, cfg.pressure)

            # Draw isoline
            ax.plot(t, w, iso.style, color=color, lw=0.8)

    # ------------------------------------------------------------------
    # Wet-bulb temperature isolines (Twb = constant)
    # ------------------------------------------------------------------
    elif key == "wet_bulb":
        for twb in iso.values:
            # Saturation humidity ratio at wet-bulb temperature
            W_sat = Psychrometrics.humidity_ratio(twb, 1.0, cfg.pressure)

            # Enthalpy at wet-bulb temperature
            h_wb = Psychrometrics.enthalpy(twb, W_sat)

            # Humidity ratio as a function of dry-bulb temperature
            W_line = (h_wb - Psychrometrics.cp * t) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * t
            )

            # Physical masking below saturation
            mask = W_line < w_sat

            ax.plot(
                t[mask],
                W_line[mask],
                iso.style,
                color=iso.color or "gray",
                lw=0.8
            )

    # ------------------------------------------------------------------
    # Enthalpy isolines (h = constant)
    # ------------------------------------------------------------------
    elif key == "enthalpy":
        for h in iso.values:
            # Analytical enthalpy relation
            W_line = (h - Psychrometrics.cp * t) / (
                Psychrometrics.Hfg + Psychrometrics.cp_v * t
            )

            # Physical masking
            mask = (W_line > 0) & (W_line < w_sat)

            ax.plot(
                t[mask],
                W_line[mask],
                iso.style,
                color=iso.color or "steelblue",
                lw=0.8
            )

    # ------------------------------------------------------------------
    # Specific volume isolines (v = constant)
    # ------------------------------------------------------------------
    elif key == "specific_volume":
        for v in iso.values:
            # Convert dry-bulb temperature to Kelvin
            T_K = t + 273.15

            # Analytical relation for humidity ratio
            W_line = (v * cfg.pressure / (Psychrometrics.Rd * T_K) - 1) / 1.6078

            # Physical masking
            mask = (W_line > 0) & (W_line < w_sat)

            ax.plot(
                t[mask],
                W_line[mask],
                iso.style,
                color=iso.color or "green",
                lw=0.8
            )

    # ------------------------------------------------------------------
    # Moisture quantity isolines (W = constant)
    # ------------------------------------------------------------------
    elif key == "moisture_quantity":
        for w_val in iso.values:
            # Horizontal lines in humidity ratio space
            ax.hlines(
                y=w_val,
                xmin=cfg.t_min,
                xmax=cfg.t_max,
                colors=iso.color or "green",
                linestyles=iso.style,
                lw=0.8,
                zorder=3
            )

def _draw_index_isolines(self, ax, index_cfg):
    """
    Draw isolines of a bioclimatic index on a psychrometric chart.

    This internal helper method is responsible for rendering **index-based
    isolines** (e.g., ITU, THI, HLI) over the psychrometric chart domain.

    The method evaluates the selected index on a regular (T, RH) grid
    and draws contour lines corresponding to the levels defined in
    :class:`IndexConfig`.

    This method is intentionally narrow in scope and imperative.
    It does NOT:
    - validate the index configuration
    - infer contour levels automatically
    - manage legends, colorbars, or layout
    - handle multiple indices generically

    Index dispatching and high-level orchestration must be handled
    by the caller.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes where the isolines will be drawn.
    index_cfg : IndexConfig
        Configuration object defining which index should be rendered
        and how (levels, style, color).

    Notes
    -----
    - This implementation currently supports **only the ITU index**.
    - The index computation is delegated to the corresponding
      index class (e.g., :class:`psychchart.indexes.ITU`).
    - The grid resolution is fixed and may be made configurable
      in future versions.
    - Relative humidity is expressed in the range [0, 1].

    Design considerations
    ---------------------
    - This method operates in (T, RH) space, not in humidity ratio.
    - All physical assumptions (pressure, constants) are inherited
      implicitly from the index implementation.
    - The method is intentionally private (prefixed with ``_``)
      to allow future refactoring without breaking the public API.

    Examples
    --------
    Typical internal usage within a plotting routine:

    >>> fig, ax = plt.subplots()
    >>> idx_cfg = IndexConfig(
    ...     name="ITU",
    ...     mode="isolines",
    ...     levels=[68, 72, 76, 80],
    ...     style=":",
    ...     color="black"
    ... )
    >>> self._draw_index_isolines(ax, idx_cfg)

    The caller is responsible for:
    - setting axis limits
    - managing legends
    - combining index isolines with other chart elements
    """

    # Local import to avoid hard dependency at module import time
    # and to keep index implementations loosely coupled.
    from psychchart.indexes import ITU
    import numpy as np

    # ------------------------------------------------------------------
    # Index dispatching
    # ------------------------------------------------------------------
    # This method currently supports only ITU.
    # Other indices (THI, HLI, UTCI, etc.) should be added explicitly
    # or refactored into a registry-based approach.
    if index_cfg.name != "ITU":
        return

    # ------------------------------------------------------------------
    # Build computational grid
    # ------------------------------------------------------------------
    # Temperature domain (°C) taken from chart configuration
    T = np.linspace(self.cfg.t_min, self.cfg.t_max, 200)

    # Relative humidity domain (fraction, not percentage)
    RH = np.linspace(0.01, 1.0, 200)

    # Create 2D grid for index evaluation
    TT, RR = np.meshgrid(T, RH)

    # ------------------------------------------------------------------
    # Index computation
    # ------------------------------------------------------------------
    # Compute ITU over the (T, RH) grid.
    # The index implementation encapsulates the physical formulation.
    Z = ITU.compute(TT, RR)

    # ------------------------------------------------------------------
    # Draw contour lines (isolines)
    # ------------------------------------------------------------------
    cs = ax.contour(
        TT,
        RR,
        Z,
        levels=index_cfg.levels,
        linestyles=index_cfg.style,
        colors=index_cfg.color,
    )

    # ------------------------------------------------------------------
    # Label isolines directly on the chart
    # ------------------------------------------------------------------
    ax.clabel(cs, fmt="ITU = %.0f")
    
def _get_index_callable(self, name):
    """
    Resolve and return a callable for a bioclimatic index.

    This internal helper method maps an **index identifier** (string)
    to a callable function that evaluates the corresponding index
    over arrays of dry-bulb temperature and relative humidity.

    The returned callable always follows the unified signature::

        f(T, RH) -> ndarray

    where:
    - ``T``  is dry-bulb temperature (°C)
    - ``RH`` is relative humidity (0–1)

    This method acts as a **dispatch layer** between high-level chart
    logic and concrete index implementations.

    This method is intentionally narrow and explicit.
    It does NOT:
    - perform index computation itself
    - validate meteorological inputs
    - normalize units
    - support dynamic or plugin-based indices

    Adding support for new indices requires extending this method.

    Parameters
    ----------
    name : str
        Identifier of the index to be resolved.
        Supported values currently include:
        - ``"ITU"`` : Temperature–Humidity Index
        - ``"HLI"`` : Heat Load Index

    Returns
    -------
    callable
        A function with signature ``f(T, RH)`` that computes the
        requested index and returns a NumPy array.

    Raises
    ------
    ValueError
        If the requested index name is not supported.

    Notes
    -----
    - Index-specific auxiliary variables (e.g., solar radiation,
      wind speed) are injected via ``self.cfg`` when required.
    - This design keeps index implementations decoupled from the
      plotting and configuration layers.
    - The method is private (prefixed with ``_``) to allow future
      refactoring without breaking the public API.

    Design considerations
    ---------------------
    - Explicit ``if`` dispatching is preferred over reflection or
      dynamic imports to preserve scientific transparency.
    - The returned callable normalizes all indices to a common
      interface, simplifying downstream contouring and masking.

    Examples
    --------
    Typical internal usage when drawing index isolines:

    >>> f = self._get_index_callable("ITU")
    >>> Z = f(TT, RH)

    For indices requiring additional environmental parameters:

    >>> f = self._get_index_callable("HLI")
    >>> Z = f(TT, RH)

    In both cases, the caller does not need to know the internal
    details of the index formulation.
    """

    # ------------------------------------------------------------------
    # Local imports to avoid hard dependencies at module import time
    # and to keep index implementations loosely coupled.
    # ------------------------------------------------------------------
    from psychchart.indexes import ITU, HLI

    # ------------------------------------------------------------------
    # Temperature–Humidity Index (ITU)
    # ------------------------------------------------------------------
    if name == "ITU":
        # ITU depends only on dry-bulb temperature and relative humidity
        return lambda T, RH: ITU.compute(T, RH)

    # ------------------------------------------------------------------
    # Heat Load Index (HLI)
    # ------------------------------------------------------------------
    if name == "HLI":
        # HLI depends on additional environmental parameters
        # retrieved from the global chart configuration.
        return lambda T, RH: HLI.compute(
            T,
            RH,
            SR=self.cfg.solar_radiation,
            WS=self.cfg.wind_speed
        )

    # ------------------------------------------------------------------
    # Unsupported index
    # ------------------------------------------------------------------
    raise ValueError(f"Unknown index: {name}")

def _draw_index_zone(self, ax, zone):
    """
    Render a filled index-based zone on the psychrometric chart.

    This internal helper method draws a **filled region** corresponding
    to a given :class:`IndexZone`, based on the numeric range of a
    bioclimatic or thermal index (e.g., ITU, HLI).

    The method evaluates the selected index over a regular (T, RH) grid
    and fills the region where the index value lies within the interval
    defined by ``zone.range``.

    This method is intentionally imperative and low-level.
    It does NOT:
    - validate the index zone definition
    - verify physical consistency of index values
    - generate legends or colorbars
    - manage overlaps between multiple index zones
    - clip against the saturation curve

    All orchestration and ordering must be handled by the caller.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes where the index zone will be rendered.
    zone : IndexZone
        Index-based zone definition, including:
        - index identifier
        - numeric range of index values
        - visual attributes (color, alpha)

    Notes
    -----
    - Index evaluation is delegated to the callable returned by
      :meth:`_get_index_callable`.
    - The grid resolution is fixed (300 × 300) and chosen as a
      compromise between visual smoothness and performance.
    - Relative humidity is treated as a fraction (0–1).
    - This method assumes that all required auxiliary variables
      (e.g., wind speed, solar radiation) are available in ``self.cfg``.

    Design considerations
    ---------------------
    - This method operates purely in (T, RH) space and does not
      transform coordinates to humidity ratio.
    - Filled regions are rendered using ``contourf`` with exactly
      two levels, corresponding to the lower and upper bounds
      of the index zone.
    - The method is private (prefixed with ``_``) to allow future
      refactoring without breaking the public API.

    Examples
    --------
    Typical internal usage when rendering index-based comfort zones:

    >>> zone = IndexZone(
    ...     index="ITU",
    ...     name="Heat stress",
    ...     range=(72.0, 78.0),
    ...     color="orange",
    ...     alpha=0.3
    ... )
    >>> self._draw_index_zone(ax, zone)

    The caller is responsible for:
    - initializing ``self._index_zone_counter``
    - controlling drawing order relative to isolines and zones
    - ensuring consistent labeling across multiple index zones
    """

    # ------------------------------------------------------------------
    # Local import to keep dependencies localized and explicit
    # ------------------------------------------------------------------
    import numpy as np

    # ------------------------------------------------------------------
    # Resolve index callable
    # ------------------------------------------------------------------
    # Returns a function f(T, RH) that computes the desired index.
    f = self._get_index_callable(zone.index)

    # ------------------------------------------------------------------
    # Build computational grid
    # ------------------------------------------------------------------
    # Dry-bulb temperature domain (°C)
    T = np.linspace(self.cfg.t_min, self.cfg.t_max, 300)

    # Relative humidity domain (fraction)
    RH = np.linspace(0.01, 1.0, 300)

    # Create 2D grid for index evaluation
    TT, RR = np.meshgrid(T, RH)

    # ------------------------------------------------------------------
    # Index computation
    # ------------------------------------------------------------------
    Z = f(TT, RR)

    # ------------------------------------------------------------------
    # Draw filled contour corresponding to the index zone range
    # ------------------------------------------------------------------
    ax.contourf(
        TT,
        RR,
        Z,
        levels=[zone.range[0], zone.range[1]],
        colors=[zone.color],
        alpha=zone.alpha,
    )

    # ------------------------------------------------------------------
    # Optional textual label (stacked in axes-relative coordinates)
    # ------------------------------------------------------------------
    ax.text(
        0.01,
        0.99 - 0.05 * self._index_zone_counter,
        f"{zone.index}: {zone.name}",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
    )

    # Increment internal counter to avoid label overlap
    self._index_zone_counter += 1

def _compute_index_field(self, index_name):
    """
    Compute a bioclimatic index over a regular psychrometric grid.

    This internal helper method evaluates a **continuous bioclimatic
    or thermal index** (e.g., ITU, HLI, THI) over a two-dimensional
    grid defined in dry-bulb temperature and relative humidity space.

    The resulting grid is intended to be used for:
    - continuous index fields (heatmaps)
    - filled contours
    - diagnostic analyses
    - index-based masking or classification

    This method is intentionally computational and low-level.
    It does NOT:
    - perform any rendering
    - normalize or clip index values
    - validate the index name
    - apply colormaps or colorbars
    - manage memory or caching

    All visualization and post-processing must be handled
    by the calling routine.

    Parameters
    ----------
    index_name : str
        Identifier of the index to be computed.
        The identifier is resolved via :meth:`_get_index_callable`.

    Returns
    -------
    TT : numpy.ndarray
        Two-dimensional array of dry-bulb temperatures (°C),
        as produced by ``numpy.meshgrid``.
    RR : numpy.ndarray
        Two-dimensional array of relative humidity values (0–1),
        as produced by ``numpy.meshgrid``.
    Z : numpy.ndarray
        Two-dimensional array of computed index values corresponding
        to each (T, RH) grid point.

    Notes
    -----
    - The grid resolution is fixed at 300 × 300 points.
    - Relative humidity is treated as a fraction (not percentage).
    - All physical assumptions and auxiliary parameters are encapsulated
      within the index implementation itself.
    - This method assumes that any required environmental parameters
      (e.g., wind speed, solar radiation) are already available
      in ``self.cfg``.

    Design considerations
    ---------------------
    - This method centralizes index field computation to avoid
      duplication across rendering functions.
    - Returning the full grid explicitly allows flexible reuse
      (fields, contours, zones).
    - The method is private (prefixed with ``_``) to allow future
      optimization or refactoring without breaking the public API.

    Examples
    --------
    Typical internal usage for rendering a continuous index field:

    >>> TT, RR, Z = self._compute_index_field("HLI")
    >>> ax.contourf(TT, RR, Z, levels=20, cmap="inferno")

    Usage for diagnostic or debugging purposes:

    >>> TT, RR, Z = self._compute_index_field("ITU")
    >>> Z.min(), Z.max()
    """

    # ------------------------------------------------------------------
    # Local import to keep dependencies explicit and localized
    # ------------------------------------------------------------------
    import numpy as np

    # ------------------------------------------------------------------
    # Resolve index callable
    # ------------------------------------------------------------------
    # Returns a function f(T, RH) that computes the requested index.
    f = self._get_index_callable(index_name)

    # ------------------------------------------------------------------
    # Build computational grid
    # ------------------------------------------------------------------
    # Dry-bulb temperature domain (°C)
    T = np.linspace(self.cfg.t_min, self.cfg.t_max, 300)

    # Relative humidity domain (fraction)
    RH = np.linspace(0.01, 1.0, 300)

    # Create 2D grid for index evaluation
    TT, RR = np.meshgrid(T, RH)

    # ------------------------------------------------------------------
    # Index computation
    # ------------------------------------------------------------------
    Z = f(TT, RR)

    return TT, RR, Z

def _draw_index_field(self, ax, field):
    """
    Render a continuous index field (heatmap) on the psychrometric chart.

    This internal helper method draws a **continuous scalar field**
    representing a bioclimatic or thermal index (e.g., ITU, HLI)
    evaluated over the psychrometric chart domain.

    Depending on the configuration provided by :class:`IndexField`,
    the field can be rendered as:
    - a filled contour map (``contourf``), or
    - a pixel-based heatmap (``pcolormesh``)

    This method is intentionally imperative and rendering-focused.
    It does NOT:
    - compute index values directly
    - validate index field configuration
    - clip values against physical limits
    - manage drawing order relative to other layers
    - normalize or rescale index values beyond Matplotlib defaults

    All orchestration and ordering must be handled by the caller.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Matplotlib axes where the index field will be rendered.
    field : IndexField
        Configuration object describing how the index field
        should be visualized, including colormap, transparency,
        normalization limits, and colorbar settings.

    Notes
    -----
    - Index computation is delegated to :meth:`_compute_index_field`.
    - Relative humidity is treated as a fraction (0–1).
    - This method assumes that ``self.fig`` exists and refers to
      the Matplotlib figure containing ``ax``.
    - Colorbar rendering is optional and controlled by ``field.colorbar``.

    Design considerations
    ---------------------
    - ``contourf`` is used when discrete levels are provided,
      enabling stepped visualization.
    - ``pcolormesh`` is used for continuous fields when no levels
      are specified.
    - This method does not apply saturation masking; values above
      100 % RH may be present unless handled elsewhere.
    - The method is private (prefixed with ``_``) to allow future
      refactoring without breaking the public API.

    Examples
    --------
    Typical internal usage for rendering an index field:

    >>> field = IndexField(
    ...     index="HLI",
    ...     cmap="inferno",
    ...     vmin=60,
    ...     vmax=100,
    ...     alpha=0.5,
    ...     colorbar=True
    ... )
    >>> self._draw_index_field(ax, field)

    Rendering ITU as a discretized field:

    >>> field = IndexField(
    ...     index="ITU",
    ...     levels=20,
    ...     cmap="plasma"
    ... )
    >>> self._draw_index_field(ax, field)
    """

    # ------------------------------------------------------------------
    # Local import to keep dependencies explicit and localized
    # ------------------------------------------------------------------
    import numpy as np

    # ------------------------------------------------------------------
    # Compute index field on the psychrometric grid
    # ------------------------------------------------------------------
    TT, RR, Z = self._compute_index_field(field.index)

    # ------------------------------------------------------------------
    # Render field using filled contours (discrete levels)
    # ------------------------------------------------------------------
    if field.levels:
        cs = ax.contourf(
            TT,
            RR,
            Z,
            levels=field.levels,
            cmap=field.cmap,
            alpha=field.alpha,
            vmin=field.vmin,
            vmax=field.vmax,
        )

    # ------------------------------------------------------------------
    # Render field using pcolormesh (continuous field)
    # ------------------------------------------------------------------
    else:
        cs = ax.pcolormesh(
            TT,
            RR,
            Z,
            shading="auto",
            cmap=field.cmap,
            alpha=field.alpha,
            vmin=field.vmin,
            vmax=field.vmax,
        )

    # ------------------------------------------------------------------
    # Optional colorbar
    # ------------------------------------------------------------------
    if field.colorbar:
        cbar = self.fig.colorbar(cs, ax=ax)
        cbar.set_label(field.index)

# =============================================================================
# Main plotting class
# =============================================================================
@dataclass
class PsychChart:
    """
    Psychrometric chart rendering engine.

    This class represents the **main orchestration layer** of the
    psychrometric chart system. It coordinates configuration objects,
    geometric constructions, and low-level drawing routines to produce
    a complete psychrometric diagram.

    The class follows a clear separation of responsibilities:
    - configuration is provided via dataclasses
    - numerical formulations are delegated to ``Psychrometrics``
    - geometric helpers handle polygons and isolines
    - this class only orchestrates and renders

    This model is intentionally imperative.
    It does NOT:
    - validate configuration objects
    - compute psychrometric properties itself
    - manage file I/O (saving figures)
    - provide interactive features

    Parameters
    ----------
    cfg : ChartConfig
        Global chart configuration defining domain limits,
        pressure, output resolution, and visual style.
    isolines : dict of str -> IsoSet, optional
        Mapping between isoline identifiers and ``IsoSet`` definitions.
        Keys must match those expected by the isoline dispatcher
        (e.g., ``"relative_humidity"``, ``"enthalpy"``).
    zones : list of Zone, optional
        List of geometric zones to be highlighted in the chart.
    points : list of Point, optional
        List of reference points (observations or design states)
        to be plotted.
    indexes : list of IndexConfig, optional
        List of thermal or bioclimatic index configurations to be
        rendered on top of the psychrometric chart (e.g., ITU isolines).
    Notes
    -----
    - This class assumes that all inputs are valid and consistent.
    - Any validation or semantic checks must be performed externally.
    - The class is designed for batch rendering, not interactive use.
    """

    # ------------------------------------------------------------------
    # Global chart configuration
    # ------------------------------------------------------------------
    cfg: ChartConfig

    # ------------------------------------------------------------------
    # Psychrometric isolines (RH, enthalpy, etc.)
    # ------------------------------------------------------------------
    isolines: Dict[str, IsoSet] | None = None

    # ------------------------------------------------------------------
    # Geometric zones (T–RH based)
    # ------------------------------------------------------------------
    zones: List[Zone] | None = None

    # ------------------------------------------------------------------
    # Reference points (observations, scenarios)
    # ------------------------------------------------------------------
    points: List[Point] | None = None

    # ------------------------------------------------------------------
    # Optional list of thermal / bioclimatic indexes
    # ------------------------------------------------------------------
    indexes: List[IndexConfig] | None = None

    # ------------------------------------------------------------------
    # Index-derived zones (K6)
    # ------------------------------------------------------------------
    index_zones: List[IndexZone] | None = None

    # ------------------------------------------------------------------
    # Continuous index fields / heatmaps (K7)
    # ------------------------------------------------------------------
    index_fields: List[IndexField] | None = None


    # ------------------------------------------------------------------
    def __post_init__(self):
        """
        Normalize optional inputs after dataclass initialization.

        This method ensures that optional containers are always
        initialized to empty collections, avoiding ``None`` checks
        throughout the rendering logic.
        """
        self.isolines = self.isolines or {}
        self.zones = self.zones or []
        self.points = self.points or []
        self.indexes = self.indexes or []
        self.index_zones = self.index_zones or []
        self.index_fields = self.index_fields or []
    # ------------------------------------------------------------------
    def draw(self) -> Axes:
        """
        Render the full psychrometric chart.

        This method orchestrates the complete rendering pipeline:
        1. Apply plotting style
        2. Initialize figure and axes
        3. Draw saturation curve
        4. Draw isolines
        5. Draw zones
        6. Draw reference points
        7. Configure axes, grid, legend, and secondary axis

        Returns
        -------
        ax : matplotlib.axes.Axes
            Axes containing the rendered psychrometric diagram.

        Notes
        -----
        - The figure object is created internally but not returned.
        - Saving or displaying the figure must be handled by the caller.
        """
        
        _index_zone_counter = 0

        # --------------------------------------------------------------
        # Apply Matplotlib style (if defined)
        # --------------------------------------------------------------
        if self.cfg.style:
            plt.style.use(self.cfg.style)

        # --------------------------------------------------------------
        # Prepare temperature axis and figure
        # --------------------------------------------------------------
        t = np.linspace(self.cfg.t_min, self.cfg.t_max, 600)
        fig, ax = plt.subplots(figsize=(12, 7))

        # --------------------------------------------------------------
        # Saturation curve (100 % relative humidity)
        # --------------------------------------------------------------
        w_sat = Psychrometrics.humidity_ratio(
            t, np.ones_like(t), self.cfg.pressure
        )
        ax.plot(t, w_sat, lw=2, color="orange", label="100 % RH")

        # --------------------------------------------------------------
        # Draw index fields
        # --------------------------------------------------------------
        for field in self.index_fields:
            _draw_index_field(ax, field)
            
        # --------------------------------------------------------------
        # Draw Indexes
        # --------------------------------------------------------------
        for idx in self.indexes:
            if idx.mode == "isolines":
                _draw_index_isolines(ax, idx)

        # --------------------------------------------------------------
        # Draw isolines
        # --------------------------------------------------------------
        for key, iso in self.isolines.items():
            if not iso.enabled:
                continue
            _draw_isoline(ax, key, iso, t, self.cfg)
            

        # --------------------------------------------------------------
        # Draw zones
        # --------------------------------------------------------------
        for z in self.zones:

            # Explicit polygon vertices
            if z.vertices:
                verts = np.asarray(z.vertices)
                t_poly = verts[:, 0]
                rh_vals = verts[:, 1]

                # Convert RH to humidity ratio
                w_poly = Psychrometrics.humidity_ratio(
                    t_poly, rh_vals, self.cfg.pressure
                )

                # Ensure polygon closure
                if not np.allclose(verts[0], verts[-1]):
                    t_poly = np.append(t_poly, t_poly[0])
                    w_poly = np.append(w_poly, w_poly[0])

            # RH-following zone
            elif z.follow_rh and z.t_range and z.rh_range:
                t_poly, w_poly = _zone_polygon_rh(z, self.cfg.pressure)

            # Rectangular zone in T–RH space
            elif z.t_range and z.rh_range:
                t_lo, t_hi = z.t_range
                rh_lo, rh_hi = z.rh_range

                t_poly = [t_lo, t_hi, t_hi, t_lo, t_lo]
                w_poly = [
                    Psychrometrics.humidity_ratio(t_lo, rh_lo, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_hi, rh_lo, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_hi, rh_hi, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_lo, rh_hi, self.cfg.pressure),
                    Psychrometrics.humidity_ratio(t_lo, rh_lo, self.cfg.pressure),
                ]

            else:
                raise ValueError(f"Zone '{z.name}' is ill-defined.")

            # Draw zone boundary
            ax.plot(
                t_poly,
                w_poly,
                lw=z.linewidth,
                color=z.edgecolor,
                label=z.name
            )

            # Fill zone interior (if requested)
            if z.facecolor and z.facecolor.lower() != "none":
                ax.fill(
                    t_poly,
                    w_poly,
                    facecolor=z.facecolor,
                    alpha=0.20
                )

        # --------------------------------------------------------------
        # Draw reference points
        # --------------------------------------------------------------
        for p in self.points:
            w_p = Psychrometrics.humidity_ratio(
                p.t, p.rh, self.cfg.pressure
            )

            ax.scatter(
                p.t, w_p,
                marker=p.marker,
                color=p.color,
                zorder=5
            )

            ax.text(
                p.t,
                w_p,
                f" {p.label}",
                va="center",
                ha="left",
                fontsize=9,
                color=p.color
            )

        # --------------------------------------------------------------
        # Axis labels and limits
        # --------------------------------------------------------------
        ax.set_xlabel("Dry-bulb temperature (°C)")
        ax.set_ylabel("Humidity ratio (kg vapor / kg dry air)")
        ax.set_xlim(self.cfg.t_min, self.cfg.t_max)

        y_min = self.cfg.y_min if self.cfg.y_min is not None else 0.0
        if self.cfg.y_max is not None:
            y_max = self.cfg.y_max
        else:
            y_max = (
                Psychrometrics.humidity_ratio(
                    self.cfg.t_max, 1.0, self.cfg.pressure
                ) * 1.05
            )

        ax.set_ylim(y_min, y_max)

        # --------------------------------------------------------------
        # Grid, legend, and secondary axis
        # --------------------------------------------------------------
        ax.grid(True, ls="--", lw=0.5)
        ax.legend(loc="upper left")

        # Secondary Y-axis (mirrored humidity ratio)
        ax2 = ax.twinx()
        ax2.set_ylim(ax.get_ylim())
        ax2.set_ylabel(
            "Humidity ratio (kg vapor / kg dry air) — right axis"
        )

        return ax


# =============================================================================
# Usage examples
# =============================================================================
#
# Example 1: Minimal chart
#
# >>> import matplotlib.pyplot as plt
# >>> from psychchart import ChartConfig, IsoSet, PsychChart
# >>> cfg = ChartConfig(t_min=0, t_max=40)
# >>> isos = {
# ...     "relative_humidity": IsoSet(
# ...         name="relative_humidity",
# ...         values=[0.3, 0.5, 0.7, 0.9],
# ...         style="--"
# ...     )
# ... }
# >>> chart = PsychChart(cfg, isolines=isos)
# >>> ax = chart.draw()
# >>> plt.show()
#
#
# Example 2: Chart with zones and points
#
# >>> import matplotlib.pyplot as plt
# >>> from psychchart import Zone, Point
# >>> comfort = Zone(
# ...     name="Comfort",
# ...     t_range=(18, 26),
# ...     rh_range=(0.4, 0.7),
# ...     facecolor="lightgreen",
# ...     edgecolor="green"
# ... )
# >>> ref = Point(label="Observed", t=30, rh=0.65, color="red")
# >>> chart = PsychChart(cfg, isolines=isos, zones=[comfort], points=[ref])
# >>> chart.draw()
# >>> plt.show()
#

