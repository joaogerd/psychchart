"""
Centralized legend assembly for psychchart.

This module builds the final chart legend from:

1. automatic renderer handles returned by low-level data renderers
2. declarative manual entries stored in ``ChartConfig.legend``

Legend classes can be expanded dynamically from semantic classification
profiles.

The module is intentionally responsible only for legend composition. It does
not draw chart data or compute scientific quantities.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Iterable, List, Tuple

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from psychchart.semantics.profiles import get_classification_profile


LegendItem = Tuple[object, str]


def _build_manual_legend_items(entry) -> List[LegendItem]:
    """
    Convert one declarative legend entry into one or more ``(handle, label)`` pairs.

    Parameters
    ----------
    entry : LegendEntry
        One validated declarative legend entry.

    Returns
    -------
    list of tuple
        One or more ``(handle, label)`` pairs.

    Notes
    -----
    This helper always returns a list, even when the entry expands to a single
    row. That keeps legend assembly uniform and avoids mixed container shapes.
    """
    if entry.type == "patch":
        return [
            (
                Patch(
                    facecolor=entry.facecolor,
                    edgecolor=entry.edgecolor,
                ),
                entry.label,
            )
        ]

    if entry.type == "line":
        return [
            (
                Line2D(
                    [0],
                    [0],
                    color=entry.color,
                    alpha=entry.alpha,
                    linewidth=entry.linewidth,
                    linestyle=entry.linestyle,
                ),
                entry.label,
            )
        ]

    if entry.type == "marker":
        return [
            (
                Line2D(
                    [0],
                    [0],
                    marker=entry.marker,
                    linestyle="None",
                    markerfacecolor=entry.markerfacecolor,
                    markeredgecolor=entry.markeredgecolor,
                    markeredgewidth=entry.markeredgewidth,
                    markersize=entry.markersize,
                ),
                entry.label,
            )
        ]

    if entry.type == "classes_from_profile":
        profile = get_classification_profile(entry.profile)
        return [
            (
                Patch(
                    facecolor=rule.color,
                    edgecolor="none",
                ),
                rule.label,
            )
            for rule in profile.rules
        ]

    raise ValueError(f"Unsupported legend entry type: {entry.type!r}")


def _normalize_auto_handles(auto_handles: Iterable | None) -> List[LegendItem]:
    """
    Normalize renderer-returned automatic handles into ``(handle, label)`` pairs.

    Parameters
    ----------
    auto_handles : iterable or None
        Raw handles returned by renderers.

    Returns
    -------
    list of tuple
        Normalized ``(handle, label)`` pairs.
    """
    if auto_handles is None:
        return []

    items: List[LegendItem] = []

    for handle in auto_handles:
        if handle is None:
            continue

        label = getattr(handle, "get_label", lambda: None)()
        if not label or str(label).startswith("_"):
            continue

        items.append((handle, str(label)))

    return items


def _deduplicate_items(items: Iterable[LegendItem]) -> List[LegendItem]:
    """
    Deduplicate legend items by label, preserving first-occurrence order.

    Parameters
    ----------
    items : iterable of tuple
        Sequence of ``(handle, label)`` pairs.

    Returns
    -------
    list of tuple
        Deduplicated ``(handle, label)`` pairs.
    """
    unique: OrderedDict[str, object] = OrderedDict()

    for handle, label in items:
        if label not in unique:
            unique[label] = handle

    return [(handle, label) for label, handle in unique.items()]


def draw_chart_legend(ax: Axes, cfg, auto_handles: Iterable | None = None) -> None:
    """
    Draw the final chart legend from automatic handles plus manual entries.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    cfg : ChartConfig
        Validated chart configuration.
    auto_handles : iterable, optional
        Raw handles returned by renderers during the drawing pipeline.
    """
    legend_cfg = getattr(cfg, "legend", None)
    if legend_cfg is None or not legend_cfg.show:
        return

    items = _normalize_auto_handles(auto_handles)

    if legend_cfg.entries:
        for entry in legend_cfg.entries:
            items.extend(_build_manual_legend_items(entry))

    items = _deduplicate_items(items)
    if not items:
        return

    handles = [handle for handle, _label in items]
    labels = [_label for _handle, _label in items]

    legend = ax.legend(
        handles,
        labels,
        loc=legend_cfg.loc,
        title=legend_cfg.title,
        frameon=legend_cfg.frameon,
        fancybox=legend_cfg.fancybox,
        framealpha=legend_cfg.framealpha,
        borderpad=legend_cfg.borderpad,
        labelspacing=legend_cfg.labelspacing,
        handlelength=legend_cfg.handlelength,
        handletextpad=legend_cfg.handletextpad,
        borderaxespad=legend_cfg.borderaxespad,
        fontsize=legend_cfg.fontsize,
        title_fontsize=legend_cfg.title_fontsize,
    )

    frame = legend.get_frame()
    frame.set_linewidth(0.8)
    frame.set_edgecolor("0.75")
    frame.set_facecolor("white")
