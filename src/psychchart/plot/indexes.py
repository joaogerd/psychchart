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

from psychchart.config.indexes import FieldRenderConfig, IsolineRenderConfig
from psychchart.render.build_index_field import build_index_field
from psychchart.plot.index_profiles import get_index_profile
from psychchart.indexes.registry import INDEX_REGISTRY
from psychchart.indexes.base import BaseIndex
from .layers import ZORDER
from .operational_zones import draw_operational_zones


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


def _resolve_field_label_position(position, fallback_label: str) -> tuple[float | None, float | None, str, float | None]:
    """
    Normalize one manual label position.
    """
    x = position.x if position.x is not None else position.t
    y = position.y if position.y is not None else position.w
    label = position.label or fallback_label
    return x, y, label, position.rotation


def _draw_index_field_labels(ax: Axes, field_cfg, levels, labels) -> None:
    """
    Draw semantic class labels inside the psychrometric diagram.
    """
    if not field_cfg.labels or not levels or not labels:
        return

    n_intervals = len(levels) - 1
    if len(labels) != n_intervals:
        return

    fontsize = field_cfg.label_fontsize or 24.0
    color = field_cfg.label_color or "black"
    alpha = field_cfg.label_alpha if field_cfg.label_alpha is not None else 0.82
    fontweight = field_cfg.label_fontweight or "normal"
    default_rotation = field_cfg.label_rotation if field_cfg.label_rotation is not None else -18.0
    zorder = ZORDER["index_field"] + 0.5

    manual_positions = field_cfg.label_positions or []

    for i, label in enumerate(labels):
        x = None
        y = None
        rotation = default_rotation

        if i < len(manual_positions):
            x, y, label, manual_rotation = _resolve_field_label_position(
                manual_positions[i],
                label,
            )
            if manual_rotation is not None:
                rotation = manual_rotation

        if x is None:
            x = 0.5 * (levels[i] + levels[i + 1])

        if y is None:
            y_min, y_max = ax.get_ylim()
            y = y_min + (0.22 + 0.18 * (i % 2)) * (y_max - y_min)

        ax.text(
            x,
            y,
            label,
            fontsize=fontsize,
            color=color,
            alpha=alpha,
            fontweight=fontweight,
            rotation=rotation,
            ha="center",
            va="center",
            zorder=zorder,
        )


# =============================================================================
# Continuous index fields (heatmaps)
# =============================================================================
def _draw_index_field(chart, ax: Axes, layer, cfg):
    """
    Render a continuous psychrometric index field as a background layer.
    """
    profile = get_index_profile(cfg.index)
    field_cfg = (
        cfg.render.field
        if cfg.render is not None and cfg.render.field is not None
        else FieldRenderConfig()
    )

    levels = cfg.levels or (profile.levels if profile else None)
    colors = cfg.colors or (profile.colors if profile else None)
    labels = cfg.labels or (profile.labels if profile else None)

    cmap = None
    norm = None

    if levels:
        if cfg.cmap:
            cmap = cfg.cmap
            norm = BoundaryNorm(
                levels,
                get_cmap(cmap).N if isinstance(cmap, str) else cmap.N,
            )
        elif colors:
            cmap = ListedColormap(colors)
            norm = BoundaryNorm(levels, cmap.N)
    elif cfg.cmap:
        cmap = cfg.cmap

    if norm is None and (cfg.vmin is not None or cfg.vmax is not None):
        norm = Normalize(vmin=cfg.vmin, vmax=cfg.vmax)

    if levels:
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

    _draw_index_field_labels(ax, field_cfg, levels, labels)

    if field_cfg.colorbar:
        cbar = chart.fig.colorbar(artist, ax=ax)

        if labels and levels:
            n_intervals = len(levels) - 1
            n_labels = len(labels)

            if n_labels == n_intervals:
                mids = [
                    0.5 * (levels[i] + levels[i + 1])
                    for i in range(n_intervals)
                ]
                cbar.set_ticks(mids)
                cbar.set_ticklabels(labels)

        cbar.set_label(cfg.label or cfg.index)


# =============================================================================
# Index isolines
# =============================================================================
def _draw_index_isolines(chart, ax: Axes, layer, cfg) -> None:
    """
    Draw contour lines (isolines) of a psychrometric/bioclimatic index.
    """
    profile = get_index_profile(cfg.index)
    iso_cfg = (
        cfg.render.isolines
        if cfg.render is not None and cfg.render.isolines is not None
        else IsolineRenderConfig()
    )

    levels = (
        iso_cfg.levels
        or cfg.levels
        or (profile.levels if profile else None)
    )

    if not levels:
        return

    line_color = iso_cfg.color or "black"

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


def _draw_operational_overlays(chart, ax: Axes) -> None:
    """
    Draw all configured operational overlays.

    Operational overlays are intentionally dispatched from the index rendering
    stage because they are gridded semantic fields over the same psychrometric
    domain as ITU/HLI/BGHI fields. Their z-order remains fully controlled by the
    overlay configuration, so they can be placed behind or above index fields.
    """
    overlays = getattr(chart, "operational_overlays", None) or []

    for overlay_cfg in overlays:
        draw_operational_zones(ax, chart, overlay_cfg)


# =============================================================================
# Public dispatchers
# =============================================================================
def draw_indexes(chart, ax):
    for cfg in chart.indexes:
        index_cls, layer = _get_index_layer(chart, cfg.index)

        if layer is None:
            continue

        if cfg.render and cfg.render.field:
            _draw_index_field(chart, ax, layer, cfg)

        if cfg.render and cfg.render.isolines:
            _draw_index_isolines(chart, ax, layer, cfg)

    _draw_operational_overlays(chart, ax)


def draw_index_zones(chart, ax: Axes) -> None:
    if not getattr(chart, "index_zones", None):
        return

    for zone in chart.index_zones:
        _draw_index_zone(chart, ax, zone)
