"""
Renderer for ordered paths derived from processed data layers.

This module implements dataset-driven psychrometric trajectory rendering.
"""

from __future__ import annotations

import numpy as np
from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

from psychchart.data.layer_runtime import ProcessedDataLayer


def _resolve_order_by(layer: ProcessedDataLayer, cfg) -> str | None:
    if cfg.order_by is not None:
        return cfg.order_by

    temporal = getattr(layer.config, "temporal", None)
    if temporal is not None:
        return getattr(temporal, "time_col", None)

    return None


def _sample_frame(df, every: int | None):
    if every is None or every <= 1:
        return df.reset_index(drop=True)
    return df.iloc[::every].reset_index(drop=True)


def _extract_plain_arrays(df) -> tuple[np.ndarray, np.ndarray]:
    t = df["_T"].to_numpy(dtype=float)
    w = df["_W"].to_numpy(dtype=float)
    mask = np.isfinite(t) & np.isfinite(w)
    return t[mask], w[mask]


def _extract_colored_arrays(
    df,
    color_by: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if color_by not in df.columns:
        available = ", ".join(map(str, df.columns))
        raise KeyError(
            f"Path renderer requested color_by={color_by!r}, but this column "
            f"is not present in the processed dataframe. "
            f"Available columns: {available}"
        )

    t = df["_T"].to_numpy(dtype=float)
    w = df["_W"].to_numpy(dtype=float)
    values = df[color_by].to_numpy(dtype=float)

    mask = np.isfinite(t) & np.isfinite(w) & np.isfinite(values)
    return t[mask], w[mask], values[mask]


def _draw_plain_path(
    ax: Axes,
    t: np.ndarray,
    w: np.ndarray,
    cfg,
) -> None:
    if t.size == 0:
        return

    ax.plot(
        t,
        w,
        color=cfg.color,
        alpha=cfg.alpha,
        linewidth=cfg.linewidth,
        linestyle=cfg.linestyle,
        zorder=cfg.zorder,
        label=cfg.label,
        solid_capstyle="round",
        solid_joinstyle="round",
    )


def _draw_colored_path(
    ax: Axes,
    t: np.ndarray,
    w: np.ndarray,
    values: np.ndarray,
    cfg,
) -> None:
    if t.size == 0:
        return

    if t.size < 2:
        _draw_plain_path(ax, t, w, cfg)
        return

    points = np.column_stack([t, w]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    collection = LineCollection(
        segments,
        cmap=cfg.cmap,
        linewidths=cfg.linewidth,
        linestyles=cfg.linestyle,
        alpha=cfg.alpha,
        zorder=cfg.zorder,
        capstyle="round",
        joinstyle="round",
    )

    collection.set_array(values[:-1])

    if cfg.vmin is not None or cfg.vmax is not None:
        collection.set_clim(cfg.vmin, cfg.vmax)

    if cfg.label is not None:
        collection.set_label(cfg.label)

    ax.add_collection(collection)


def _build_path_legend_handle(cfg):
    if cfg.label is None:
        return None

    if cfg.color_by is None:
        color = cfg.color
    else:
        color = colormaps[cfg.cmap](0.5)

    return Line2D(
        [0],
        [0],
        color=color,
        alpha=cfg.alpha,
        linewidth=cfg.linewidth,
        linestyle=cfg.linestyle,
        label=cfg.label,
    )


def draw_path(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> list:
    """Render one ordered path from a processed data layer."""
    order_by = _resolve_order_by(layer, cfg)
    df = layer.ordered_frame(order_by)
    df = _sample_frame(df, getattr(cfg, "every", 1))

    if cfg.color_by is None:
        t, w = _extract_plain_arrays(df)
        _draw_plain_path(ax, t, w, cfg)
    else:
        t, w, values = _extract_colored_arrays(df, cfg.color_by)
        _draw_colored_path(ax, t, w, values, cfg)

    handle = _build_path_legend_handle(cfg)
    return [handle] if handle is not None else []
