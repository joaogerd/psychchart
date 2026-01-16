"""
Index rendering utilities for psychrometric charts.

This module provides **low-level helpers** to compute and render
bioclimatic and thermal indexes (e.g., ITU, HLI) over a
psychrometric (T, RH) domain.

Design philosophy
-----------------
- Index computation is *fully decoupled* from plotting logic.
- All index evaluation happens in (T, RH) space.
- This module does NOT validate configurations.
- This module does NOT manage plotting order.
- The PsychChart object acts only as a *context provider*.

Typical responsibilities handled here:
- resolve index identifiers to callables
- build computational grids
- draw isolines, zones and continuous fields

All orchestration must be done by the caller.
"""
from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.colors import ListedColormap, BoundaryNorm

from psychchart.indexes.engine import evaluate_index
from psychchart.config import IndexConfig, IndexZone, IndexField
from psychchart.psychrometrics import Psychrometrics
from psychchart.plot.index_profiles import get_index_profile
from .layers import ZORDER


def _clip_to_saturation(ax, artist, T, W_sat):
    """
    Clip a Matplotlib artist to the saturation curve (100% relative humidity).

    This helper function restricts the visible region of a Matplotlib
    artist (e.g., a heatmap, contour field, or filled zone) to the
    **physically admissible region** of the psychrometric chart,
    i.e. the area *below* the saturation curve (RH = 100%).

    From a physical standpoint, any state above the saturation curve
    represents supersaturation and is therefore not meaningful for
    standard psychrometric analysis.

    From a visualization standpoint, clipping:
    - prevents misleading colors or contours above saturation,
    - reinforces the physical interpretation of the chart,
    - improves visual clarity and scientific correctness.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Axes to which the artist belongs. Used to ensure that
        clipping is applied in data coordinates.
    artist : matplotlib artist
        Any Matplotlib artist supporting ``set_clip_path``,
        such as:
        - QuadMesh (from ``pcolormesh``)
        - ContourSet (from ``contourf``)
        - PolyCollection
    T : numpy.ndarray
        One-dimensional array of dry-bulb temperature values (°C).
        This array must match the domain used to construct ``W_sat``.
    W_sat : numpy.ndarray
        One-dimensional array of saturation humidity ratio values
        (kg/kg) corresponding to ``T``.

    Notes
    -----
    - The clipping polygon is constructed in data coordinates.
    - The region kept visible is:
        * above the x-axis (W >= 0)
        * below the saturation curve
    - The saturation curve itself is **not modified** by this function.
    - This function does not check array consistency; validation must
      be handled by the caller.

    Design considerations
    ---------------------
    - The polygon is explicitly closed to ensure correct clipping.
    - The lower boundary is defined as W = 0 (chart baseline).
    - This function is intentionally low-level and imperative.
    - It is private (prefixed with ``_``) to allow future refactoring
      without breaking the public API.

    Examples
    --------
    Clipping a continuous index field (pcolormesh):

    >>> cs = ax.pcolormesh(TT, RR, Z, cmap="inferno")
    >>> _clip_to_saturation(ax, cs, chart.T, chart.W_sat)

    Clipping a filled contour set:

    >>> cs = ax.contourf(TT, RR, Z, levels=20)
    >>> for coll in cs.collections:
    ...     _clip_to_saturation(ax, coll, chart.T, chart.W_sat)

    Typical usage pattern inside PsychChart:

    >>> cs = ax.contourf(...)
    >>> _clip_to_saturation(self.ax, cs, self.T, self.W_sat)
    """

    # ------------------------------------------------------------------
    # Build clipping polygon
    # ------------------------------------------------------------------
    # The polygon follows:
    #   1) the saturation curve from left to right
    #   2) the chart baseline (W = 0) from right to left
    #
    # This defines the physically valid region of the chart.
    verts = np.column_stack([
        np.concatenate([T, T[::-1]]),                     # x-coordinates
        np.concatenate([W_sat, np.zeros_like(W_sat)]),    # y-coordinates
    ])

    # ------------------------------------------------------------------
    # Path codes
    # ------------------------------------------------------------------
    # MOVETO : start at first saturation point
    # LINETO : follow saturation curve
    # LINETO : return along baseline
    codes = np.concatenate([
        [Path.MOVETO],
        np.full(len(T) - 1, Path.LINETO),
        np.full(len(T), Path.LINETO),
    ])

    # ------------------------------------------------------------------
    # Create clipping path and patch
    # ------------------------------------------------------------------
    path = Path(verts, codes)

    # The transform ensures clipping occurs in data coordinates
    patch = PathPatch(path, transform=ax.transData)

    # ------------------------------------------------------------------
    # Apply clipping to the artist
    # ------------------------------------------------------------------
    artist.set_clip_path(patch)
    
def _compute_psychrometric_index_field(
    chart,
    index: str,
    *,
    params: dict | None = None,
    n: int = 300,
):    
    """
    Compute a bioclimatic index field over the psychrometric domain (T, W).

    This function evaluates a bioclimatic or thermal index over a
    **physically consistent psychrometric grid**, defined in terms of:

    - dry-bulb temperature (T)
    - humidity ratio (W)

    The index itself is evaluated in (T, RH) space, but the grid is
    constructed in (T, W) space to ensure that:
    - supersaturated states are naturally excluded,
    - clipping against saturation is geometrically well-defined,
    - the resulting field can be plotted directly in psychrometric
      coordinates.

    The conversion from humidity ratio (W) to relative humidity (RH)
    is performed using the exact psychrometric relationship.

    Parameters
    ----------
    chart : PsychChart
        Chart context providing:
        - temperature limits (cfg.t_min, cfg.t_max)
        - atmospheric pressure (cfg.pressure)
        - auxiliary variables required by some indexes
    index : str
        Identifier of the index to be computed (e.g., ``"ITU"``, ``"HLI"``).
    n : int, optional
        Resolution of the computational grid in each dimension.
        Default is 300, resulting in an n × n grid.

    Returns
    -------
    TT : numpy.ndarray
        2D array of dry-bulb temperature values (°C).
    WW : numpy.ndarray
        2D array of humidity ratio values (kg/kg).
    Z : numpy.ndarray
        2D array of computed index values.

    Notes
    -----
    - The humidity ratio grid spans from W = 0 up to the **maximum
      saturation value** within the temperature domain.
    - Relative humidity is clipped to [0, 1] after conversion to
      prevent numerical artefacts near saturation.
    - No visualization, masking, or clipping is performed here.
      This function is purely computational.

    Design considerations
    ---------------------
    - The psychrometric grid is defined in (T, W), not (T, RH),
      to preserve physical meaning and simplify saturation handling.
    - Index computation remains agnostic of plotting concerns.
    - This function is intentionally private and imperative.

    Examples
    --------
    Typical internal usage when rendering an index field:

    >>> TT, WW, Z = _compute_psychrometric_index_field(
    ...     chart,
    ...     index="ITU",
    ...     n=200,
    ... )

    The returned arrays can be passed directly to ``contourf`` or
    ``pcolormesh``:

    >>> ax.contourf(TT, WW, Z, levels=20)
    """
    if params is None:
        params = {}
        
    # ------------------------------------------------------------------
    # 1. Dry-bulb temperature domain (°C)
    # ------------------------------------------------------------------
    # This defines the horizontal axis of the psychrometric chart.
    T = np.linspace(chart.cfg.t_min, chart.cfg.t_max, n)

    # ------------------------------------------------------------------
    # 2. Saturation humidity ratio along T
    # ------------------------------------------------------------------
    # W_sat(T) defines the physical upper boundary (RH = 100%).
    W_sat = Psychrometrics.humidity_ratio(
        T,
        1.0,
        chart.cfg.pressure,
    )

    # ------------------------------------------------------------------
    # 3. Humidity ratio domain (kg/kg)
    # ------------------------------------------------------------------
    # The vertical axis spans from completely dry air (W = 0)
    # up to the maximum saturation value within the domain.
    W = np.linspace(0.0, W_sat.max(), n)

    # ------------------------------------------------------------------
    # 4. Build full psychrometric grid (T, W)
    # ------------------------------------------------------------------
    TT, WW = np.meshgrid(T, W)

    # ------------------------------------------------------------------
    # 5. Physically consistent conversion: W → RH
    # ------------------------------------------------------------------
    # Relative humidity is derived from humidity ratio using the
    # exact psychrometric relationship.
    #
    # This step is CRITICAL:
    # - Indexes are defined in terms of RH, not W.
    # - Naive interpolation in RH space would be incorrect.
    RH = Psychrometrics.relative_humidity_from_W(
        TT,
        WW,
        chart.cfg.pressure,
    )

    # ------------------------------------------------------------------
    # 6. Physical masking / clipping
    # ------------------------------------------------------------------
    # Numerical artefacts may produce values slightly outside
    # the physical range near saturation.
    RH = np.clip(RH, 0.0, 1.0)

    # ------------------------------------------------------------------
    # 8. Compute index field
    # ------------------------------------------------------------------
    Z = evaluate_index(
        index,
        TT,
        RH,
        params=params
    )

    return TT, WW, Z


# =============================================================================
# Index isolines
# =============================================================================
def _draw_index_isolines(chart, ax: Axes, config: IndexConfig):
    """
    Draw contour lines (isolines) of a bioclimatic index.

    This helper evaluates the index on a regular grid and draws
    isolines corresponding to the levels defined in ``IndexConfig``.

    Parameters
    ----------
    chart : PsychChart
        Chart context.
    ax : matplotlib.axes.Axes
        Axes where isolines will be drawn.
    config : IndexConfig
        Index configuration (levels, style, color).

    Notes
    -----
    - Contours are drawn in (T, RH) space.
    - Labels are rendered directly on the isolines.
    """

    TT, WW, Z = _compute_psychrometric_index_field(
        chart,
        config.index,
        params=config.parameters,
    )

    # Draw isolines
    cs = ax.contour(
        TT,
        WW,
        Z,
        levels=config.levels,
        linestyles=config.style,
        colors=config.color,
        zorder=ZORDER['isolines'],
    )

    # Inline labels for clarity
    ax.clabel(
        cs,
        fmt=lambda v: f"{config.name} = {v:.0f}",
        fontsize=8,
    )


# =============================================================================
# Index-based zones (categorical regions)
# =============================================================================
def _draw_index_zone(chart, ax: Axes, zone: IndexZone):
    """
    Render a filled zone corresponding to a numeric index range.

    This helper highlights regions where an index lies within
    a given interval (e.g., thermal stress classes).

    Parameters
    ----------
    chart : PsychChart
        Chart context.
    ax : matplotlib.axes.Axes
        Target axes.
    zone : IndexZone
        Index zone definition:
        - index name
        - numeric range
        - visual attributes

    Notes
    -----
    - Implemented using ``contourf`` with two levels.
    - Text labels are stacked vertically in axes coordinates.
    """

    TT, WW, Z = _compute_psychrometric_index_field(
        chart,
        zone.index,
        params=zone.parameters,
    )

    # Filled region
    ax.contourf(
        TT,
        WW,
        Z,
        levels=[zone.range[0], zone.range[1]],
        colors=[zone.color],
        alpha=zone.alpha,
        zorder=ZORDER['index_zone'],
    )

    # Stacked textual label
    ax.text(
        0.01,
        0.99 - 0.05 * chart._index_zone_counter,
        f"{zone.index}: {zone.name}",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        zorder=ZORDER["zone_edge"],
    )

    chart._index_zone_counter += 1


# =============================================================================
# Continuous index fields (heatmaps)
# =============================================================================
def _draw_index_field(chart, ax: Axes, field: IndexField):
    """
    Render a continuous psychrometric index field as a background layer.

    This helper renders a **scalar bioclimatic index** (e.g., ITU, HLI)
    evaluated over the psychrometric domain and displayed as a
    background layer behind isolines, zones and points.

    The function supports:
    - canonical semantic profiles (:class:`IndexProfile`)
    - user overrides via ``IndexField``
    - discrete (classified) or continuous visualization
    - automatic clipping to the saturation curve (RH = 100 %)
    - optional semantic colorbars

    Responsibilities
    ----------------
    - Compute index values on a psychrometric grid (T, W)
    - Resolve semantic defaults from ``IndexProfile``
    - Build colormap and normalization
    - Render the field using Matplotlib
    - Apply physical clipping (below saturation)
    - Optionally attach a labeled colorbar

    Non-responsibilities
    --------------------
    - Index computation logic (delegated elsewhere)
    - Grid generation strategy (delegated to helpers)
    - Axis formatting or layout
    - Plot ordering beyond z-order

    Parameters
    ----------
    chart : PsychChart
        Chart context providing:
        - configuration (temperature limits, pressure)
        - Matplotlib figure
        - saturation curve
    ax : matplotlib.axes.Axes
        Axes where the index field will be rendered.
    field : IndexField
        Index field configuration defining:
        - index name
        - visualization overrides
        - transparency
        - colorbar behavior

    Notes
    -----
    - Index values are computed in **psychrometric space (T, W)**,
      not (T, RH). This avoids ambiguities above saturation.
    - Saturation clipping is applied by default unless explicitly
      disabled in the associated ``IndexProfile``.
    - This function is intentionally private and imperative.
    """

    # ------------------------------------------------------------------
    # 1. Compute index field in psychrometric space (T, W)
    # ------------------------------------------------------------------
    # TT : 2D dry-bulb temperature grid (°C)
    # WW : 2D humidity ratio grid (kg/kg)
    # Z  : computed index values
    TT, WW, Z = _compute_psychrometric_index_field(
        chart,
        field.index,
        params=field.parameters,
    )

    # ------------------------------------------------------------------
    # 2. Resolve canonical semantic profile (if available)
    # ------------------------------------------------------------------
    profile = get_index_profile(field.index)

    # Priority order for classification levels:
    #   1) explicit levels from IndexField
    #   2) canonical levels from IndexProfile
    #   3) None (continuous rendering)
    levels = field.levels or (profile.levels if profile else None)

    # Colors come only from the semantic profile
    colors = profile.colors if profile else None

    # ------------------------------------------------------------------
    # 3. Build colormap and normalization
    # ------------------------------------------------------------------
    cmap = None
    norm = None

    # Discrete classified field (semantic)
    if levels and colors:
        cmap = ListedColormap(colors)
        norm = BoundaryNorm(levels, cmap.N)

    # Continuous field with user-defined colormap
    elif field.cmap:
        cmap = field.cmap

    # ------------------------------------------------------------------
    # 4. Render the index field
    # ------------------------------------------------------------------
    if levels:
        # Discrete filled contours (classified visualization)
        cs = ax.contourf(
            TT,
            WW,
            Z,
            levels=levels,
            cmap=cmap,
            norm=norm,
            alpha=field.alpha,
            zorder=ZORDER["index_field"],
            extend="max",
        )
        artist = cs
    else:
        # Continuous heatmap
        artist = ax.pcolormesh(
            TT,
            WW,
            Z,
            shading="auto",
            cmap=cmap,
            alpha=field.alpha,
            zorder=ZORDER["index_field"],
        )

    # ------------------------------------------------------------------
    # 5. Clip field to the saturation curve (RH = 100 %)
    # ------------------------------------------------------------------
    # Unless explicitly disabled by the profile, index fields
    # should never appear above the physical saturation limit.
    if profile is None or profile.clip_to_saturation:
        # Build 1D saturation curve
        T_1d = np.linspace(
            chart.cfg.t_min,
            chart.cfg.t_max,
            TT.shape[1],
        )
        W_sat = Psychrometrics.humidity_ratio(
            T_1d, 1.0, chart.cfg.pressure
        )

        _clip_to_saturation(ax, artist, T_1d, W_sat)

    # ------------------------------------------------------------------
    # 6. Optional colorbar with semantic labels
    # ------------------------------------------------------------------
    if field.colorbar:
        cbar = chart.fig.colorbar(artist, ax=ax)

        # If semantic labels are available, use class midpoints
        if profile and profile.labels and levels:
            mids = [
                0.5 * (levels[i] + levels[i + 1])
                for i in range(len(levels) - 1)
            ]
            cbar.set_ticks(mids)
            cbar.set_ticklabels(profile.labels)

        cbar.set_label(field.index)


# =============================================================================
# Public dispatchers (called by PsychChart)
# =============================================================================
def draw_index_isolines(ax: Axes, chart) -> None:
    """Draw all index isolines configured in the chart."""
    for idx in chart.indexes:
        if idx.mode == "isolines":
            _draw_index_isolines(chart, ax, idx)


def draw_index_zones(ax: Axes, chart) -> None:
    """Draw all index-based zones."""
    for zone in chart.index_zones:
        _draw_index_zone(chart, ax, zone)


def draw_index_fields(ax: Axes, chart) -> None:
    """Draw all continuous index fields."""
    for field in chart.index_fields:
        _draw_index_field(chart, ax, field)

