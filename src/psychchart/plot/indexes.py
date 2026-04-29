"""Index rendering utilities for psychrometric charts."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize
from matplotlib.pyplot import get_cmap

from psychchart.config import FieldRenderConfig, IsolineRenderConfig
from psychchart.indexes.base import BaseIndex
from psychchart.indexes.registry import INDEX_REGISTRY
from psychchart.plot.index_profiles import get_index_profile
from psychchart.render.build_index_field import build_index_field

from .layers import ZORDER
from .operational_zones import draw_operational_zones


def _resolve_index(index) -> type[BaseIndex]:
    """Resolve an index identifier to its registered index class."""
    if isinstance(index, str):
        if index not in INDEX_REGISTRY:
            raise ValueError(f"Unknown index '{index}'")
        return INDEX_REGISTRY[index]

    if isinstance(index, type) and issubclass(index, BaseIndex):
        return index

    raise TypeError(f"Invalid index type: {index}")


def _get_index_layer(chart, index):
    """Resolve an index and build/cache its scalar field layer."""
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


def _draw_index_field(chart, ax: Axes, layer, cfg):
    """Render a continuous psychrometric index field."""
    profile = get_index_profile(cfg.index)
    field_cfg = (
        cfg.render.field
        if cfg.render is not None and cfg.render.field is not None
        else FieldRenderConfig()
    )

    levels = cfg.levels or (profile.levels if profile else None)
    colors = profile.colors if profile else None

    cmap = None
    norm = None

    if levels:
        if cfg.cmap:
            cmap = cfg.cmap
            norm = BoundaryNorm(levels, get_cmap(cmap).N if isinstance(cmap, str) else cmap.N)
        elif colors:
            cmap = ListedColormap(colors)
            norm = BoundaryNorm(levels, cmap.N)
    elif cfg.cmap:
        cmap = cfg.cmap

    if norm is None and (cfg.vmin is not None or cfg.vmax is not None):
        norm = Normalize(vmin=cfg.vmin, vmax=cfg.vmax)

    alpha = 1.0 if field_cfg.alpha is None else field_cfg.alpha

    if levels:
        artist = ax.contourf(
            layer.X,
            layer.Y,
            layer.Z,
            levels=levels,
            cmap=cmap,
            norm=norm,
            alpha=alpha,
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
            alpha=alpha,
            zorder=ZORDER["index_field"],
        )

    if field_cfg.colorbar:
        cbar = chart.fig.colorbar(artist, ax=ax)

        if profile and profile.labels and levels:
            n_intervals = len(levels) - 1
            if len(profile.labels) == n_intervals:
                mids = [0.5 * (levels[i] + levels[i + 1]) for i in range(n_intervals)]
                cbar.set_ticks(mids)
                cbar.set_ticklabels(profile.labels)

        cbar.set_label(cfg.label or cfg.index)


def _draw_index_isolines(chart, ax: Axes, layer, cfg) -> None:
    """Draw contour lines of a psychrometric or bioclimatic index."""
    profile = get_index_profile(cfg.index)
    iso_cfg = (
        cfg.render.isolines
        if cfg.render is not None and cfg.render.isolines is not None
        else IsolineRenderConfig()
    )

    levels = iso_cfg.levels or cfg.levels or (profile.levels if profile else None)
    if not levels:
        return

    cs = ax.contour(
        layer.X,
        layer.Y,
        layer.Z,
        levels=levels,
        linestyles=iso_cfg.style,
        linewidths=iso_cfg.linewidth,
        colors=iso_cfg.color or "black",
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


def _index_zone_mask(layer, zone) -> np.ndarray:
    """Return the finite boolean mask selected by an index-zone interval."""
    lower, upper = zone.range
    return np.isfinite(layer.Z) & (layer.Z >= lower) & (layer.Z <= upper)


def _index_zone_facecolor(zone) -> str:
    """Return the fill color for an index zone."""
    return zone.facecolor or zone.color or "gray"


def _index_zone_label_position(chart, zone, layer, mask: np.ndarray) -> tuple[float, float] | None:
    """Return a chart-coordinate label position for an index-derived zone."""
    if zone.label_t is not None and zone.label_rh is not None:
        label_w = chart.psych.humidity_ratio(zone.label_t, zone.label_rh, chart.cfg.pressure)
        return float(zone.label_t), float(label_w)

    if zone.label_position == "manual":
        return None

    x_vals = layer.X[mask]
    y_vals = layer.Y[mask]

    if x_vals.size == 0:
        return None

    x0 = float(np.nanmedian(x_vals))
    y0 = float(np.nanmedian(y_vals))
    dist2 = (x_vals - x0) ** 2 + (y_vals - y0) ** 2
    i = int(np.nanargmin(dist2))

    return float(x_vals[i]), float(y_vals[i])


def _draw_index_zone_label(ax: Axes, chart, zone, layer, mask: np.ndarray) -> None:
    """Draw an optional label inside an index-derived region."""
    if not zone.show_label:
        return

    text = zone.label or zone.name
    if not text:
        return

    position = _index_zone_label_position(chart, zone, layer, mask)
    if position is None:
        return

    bbox = zone.label_bbox
    if bbox is None:
        bbox = {
            "boxstyle": "round,pad=0.20",
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.0,
        }

    ax.annotate(
        text,
        xy=position,
        ha="center",
        va="center",
        color=zone.label_color or zone.edgecolor or zone.color or "black",
        fontsize=zone.label_fontsize,
        fontweight=zone.label_fontweight,
        rotation=zone.label_rotation,
        bbox=bbox,
        zorder=ZORDER["zone_edge"] + 1,
    )


def _draw_index_zone(chart, ax: Axes, zone) -> None:
    """Draw a filled and optionally labeled region derived from an index interval."""
    _, layer = _get_index_layer(chart, zone.index)
    if layer is None:
        return

    mask = _index_zone_mask(layer, zone)
    if not np.any(mask):
        return

    mask_field = np.where(mask, 1.0, np.nan)

    ax.contourf(
        layer.X,
        layer.Y,
        mask_field,
        levels=[0.5, 1.5],
        colors=[_index_zone_facecolor(zone)],
        alpha=zone.alpha,
        zorder=ZORDER["index_zone"],
    )

    if zone.edgecolor and zone.linewidth > 0:
        ax.contour(
            layer.X,
            layer.Y,
            mask.astype(float),
            levels=[0.5],
            colors=[zone.edgecolor],
            linewidths=zone.linewidth,
            zorder=ZORDER["zone_edge"],
        )

    _draw_index_zone_label(ax, chart, zone, layer, mask)


def _draw_operational_overlays(chart, ax: Axes) -> None:
    """Draw all configured operational overlays."""
    overlays = getattr(chart, "operational_overlays", None) or []

    for overlay_cfg in overlays:
        draw_operational_zones(ax, chart, overlay_cfg)


def draw_indexes(chart, ax):
    """Draw all configured index fields and isolines."""
    for cfg in chart.indexes:
        _, layer = _get_index_layer(chart, cfg.index)
        if layer is None:
            continue

        if cfg.render and cfg.render.field:
            _draw_index_field(chart, ax, layer, cfg)

        if cfg.render and cfg.render.isolines:
            _draw_index_isolines(chart, ax, layer, cfg)

    _draw_operational_overlays(chart, ax)


def draw_index_zones(chart, ax: Axes) -> None:
    """Draw all configured index-derived zones."""
    if not getattr(chart, "index_zones", None):
        return

    for zone in chart.index_zones:
        _draw_index_zone(chart, ax, zone)
