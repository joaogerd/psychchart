"""
Index rendering utilities for psychrometric charts.

Pure rendering layer.

Responsibilities:
- Receive precomputed index layers (via render/)
- Draw them using matplotlib

Non-responsibilities:
- No index computation
- No grid building
- No psychrometric transformations
"""

from __future__ import annotations
import numpy as np
from matplotlib.pyplot import get_cmap
from matplotlib.axes import Axes
from matplotlib.patches import PathPatch
from matplotlib.colors import ListedColormap, BoundaryNorm, Normalize

from psychchart.render.build_index_field import build_index_field
from psychchart.plot.index_profiles import get_index_profile
from psychchart.indexes.registry import INDEX_REGISTRY
from psychchart.indexes.base import BaseIndex
from .layers import ZORDER


# =============================================================================
# Helpers
# =============================================================================
def _resolve_index(index) -> type[BaseIndex]:
    """
    Resolve index from string or class.
    """
    if isinstance(index, str):
        if index not in INDEX_REGISTRY:
            raise ValueError(f"Unknown index '{index}'")
        return INDEX_REGISTRY[index]

    if isinstance(index, type) and issubclass(index, BaseIndex):
        return index

    raise TypeError(f"Invalid index type: {index}")


def _get_index_layer(chart, index):
    """
    Resolve index and safely build its scalar field layer.

    Returns
    -------
    (index_cls, layer) or (index_cls, None)
    """
    if not hasattr(chart, "_index_cache"):
        chart._index_cache = {}

    if index in chart._index_cache:
        return _resolve_index(index), chart._index_cache[index]

    index_cls = _resolve_index(index)

    try:
        layer = build_index_field(index_cls, chart.cfg, chart.psych)
    except ValueError:
        return index_cls, None

    chart._index_cache[index] = layer

    return index_cls, layer
# =============================================================================
# Continuous index fields (heatmaps)
# =============================================================================

def _draw_index_field(chart, ax: Axes, layer, cfg: IndexConfig):
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
    # 1. Get index field in psychrometric space (T, W)
    # ------------------------------------------------------------------
    # layer.X : 2D dry-bulb temperature grid (°C)
    # layer.Y : 2D humidity ratio grid (kg/kg)
    # layer.Z : computed index values
#    _, layer = _get_index_layer(chart, cfg.index)

    # ------------------------------------------------------------------
    # 2. Resolve rendering config and semantic profile
    # ------------------------------------------------------------------
    profile = get_index_profile(cfg.index)
    field_cfg = (
        cfg.render.field
        if cfg.render is not None and cfg.render.field is not None
        else FieldRenderConfig()
    )

    # Priority for field classification levels:
    #   1) canonical levels from IndexConfig
    #   2) canonical levels from IndexProfile
    #   3) None (continuous rendering)
    levels = cfg.levels or (profile.levels if profile else None)

    # Semantic colors are taken only from the profile
    colors = profile.colors if profile else None

    # ------------------------------------------------------------------
    # 3. Build colormap and normalization
    # ------------------------------------------------------------------
    cmap = None
    norm = None

    # User-declared cmap has priority over semantic profile colors
    if levels:
        if cfg.cmap:
            cmap = cfg.cmap
            # For classified rendering with explicit levels, keep discrete bins
            norm = BoundaryNorm(levels, get_cmap(cmap).N if isinstance(cmap, str) else cmap.N)
        elif colors:
            cmap = ListedColormap(colors)
            norm = BoundaryNorm(levels, cmap.N)
    elif cfg.cmap:
        cmap = cfg.cmap
    # Optional explicit normalization bounds for continuous rendering
    if norm is None and (cfg.vmin is not None or cfg.vmax is not None):
        norm = Normalize(vmin=cfg.vmin, vmax=cfg.vmax)

    # ------------------------------------------------------------------
    # 4. Render the index field
    # ------------------------------------------------------------------
    if levels:
        # Discrete filled contours (classified visualization)
        artist = ax.contourf(
            layer.X,
            layer.Y,
            layer.Z,
            levels=levels,
            cmap=cmap,
            norm=norm,
            alpha=field_cfg.alpha,
            zorder=ZORDER["index_field"],
            extend="max",
        )
    else:
        # Continuous heatmap
        artist = ax.pcolormesh(
            layer.X,
            layer.Y,
            layer.Z,
            shading="auto",
            cmap=cmap,
            norm=norm,
            alpha=field_cfg.alpha,
            zorder=ZORDER["index_field"],
        )

    # ------------------------------------------------------------------
    # 5. Optional colorbar with semantic labels
    # ------------------------------------------------------------------
    if field_cfg.colorbar:
        cbar = chart.fig.colorbar(artist, ax=ax)
    
        if profile and profile.labels and levels:
            n_intervals = len(levels) - 1
            n_labels = len(profile.labels)
    
            if n_labels == n_intervals:
                mids = [
                    0.5 * (levels[i] + levels[i + 1])
                    for i in range(n_intervals)
                ]
                cbar.set_ticks(mids)
                cbar.set_ticklabels(profile.labels)
    
        cbar.set_label(cfg.label or cfg.index)
# =============================================================================
# Index isolines
# =============================================================================

def _draw_index_isolines(chart, ax: Axes, layer, cfg: IndexConfig) -> None:
    """
    Draw contour lines (isolines) of a psychrometric/bioclimatic index.

    This helper evaluates the index on the psychrometric grid and renders
    contour lines at the configured levels.

    Parameters
    ----------
    chart : PsychChart
        Chart context.
    ax : matplotlib.axes.Axes
        Axes where isolines will be drawn.
    cfg : IndexConfig
        Index configuration for isoline rendering.

    Notes
    -----
    - Contours are drawn in psychrometric space using the grid produced
      by the index layer.
    - Labels, when enabled, are rendered directly on the contour lines.
    """

    # ------------------------------------------------------------------
    # 1. Get index field in psychrometric space
    # ------------------------------------------------------------------
    #_, layer = _get_index_layer(chart, cfg.index)

    # ------------------------------------------------------------------
    # 2. Resolve semantic profile and isoline render config
    # ------------------------------------------------------------------
    profile = get_index_profile(cfg.index)
    iso_cfg = (
        cfg.render.isolines
        if cfg.render is not None and cfg.render.isolines is not None
        else IsolineRenderConfig()
    )

    # Priority for isoline levels:
    #   1) explicit isoline levels
    #   2) canonical index levels
    #   3) canonical semantic levels from profile
    #   4) no rendering if none exist
    levels = (
        iso_cfg.levels
        or cfg.levels
        or (profile.levels if profile else None)
    )

    if not levels:
        return

    # ------------------------------------------------------------------
    # 3. Resolve line color
    # ------------------------------------------------------------------
    # Isolines use their own rendering color, independent of semantic
    # fill colors used by the field layer.
    line_color = iso_cfg.color or "black"

    # ------------------------------------------------------------------
    # 4. Draw contour lines
    # ------------------------------------------------------------------
    cs = ax.contour(
        layer.X,
        layer.Y,
        layer.Z,
        levels=levels,
        linestyles=iso_cfg.style,
        linewidths=iso_cfg.linewidth,
        colors=line_color,
        alpha=iso_cfg.alpha,
        zorder=ZORDER["isolines"],
    )

    # ------------------------------------------------------------------
    # 5. Draw inline labels
    # ------------------------------------------------------------------
    if iso_cfg.label:
        template = iso_cfg.label_fmt or "{index} = {value:.0f}"

        ax.clabel(
            cs,
            fmt=lambda v: template.format(index=cfg.index, value=v),
            fontsize=iso_cfg.label_fontsize or 8,
        )

# =============================================================================
# Index zones
# =============================================================================
def _draw_index_zone(chart, ax: Axes, zone):
    index_cls = _resolve_index(zone.index)

    try:
        layer = build_index_field(index_cls, chart.cfg, chart.psych)
    except ValueError:
        return

    if not hasattr(zone, "range") or len(zone.range) != 2:
        raise ValueError(f"Invalid zone range for index '{zone.index}'")

    mask = (layer.Z >= zone.range[0]) & (layer.Z <= zone.range[1])

    ax.contourf(
        layer.X,
        layer.Y,
        mask,
        levels=[0.5, 1],
        colors=[zone.color],
        alpha=zone.alpha,
        zorder=ZORDER["index_zone"],
    )

    # Safe counter
    if not hasattr(chart, "_index_zone_counter"):
        chart._index_zone_counter = 0

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
# Public dispatchers
# =============================================================================
def draw_indexes(chart, ax):
    for cfg in chart.indexes:
        index_cls, layer = _get_index_layer(chart, cfg.index)

        if layer is None:
            continue

        # FIELD
        if cfg.render and cfg.render.field:
            _draw_index_field(chart, ax, layer, cfg)

        # ISOLINES
        if cfg.render and cfg.render.isolines:
            _draw_index_isolines(chart, ax, layer, cfg)



def draw_index_zones(chart, ax: Axes) -> None:
    if not getattr(chart, "index_zones", None):
        return

    for zone in chart.index_zones:
        _draw_index_zone(chart, ax, zone)
