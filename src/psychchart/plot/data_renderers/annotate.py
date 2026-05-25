"""
Renderer for periodic annotations over processed data layers.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd
from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def _coerce_datetime(value: Any) -> Any:
    """Return a datetime-like value when a scalar can be safely parsed."""
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value

    if isinstance(value, str):
        try:
            parsed = pd.to_datetime(value, errors="raise")
        except (TypeError, ValueError):
            return value

        if pd.isna(parsed):
            return value
        return parsed

    return value


def _build_annotation_context(row, cfg) -> dict[str, Any]:
    """Build the formatting context used by annotation templates.

    The public template keys remain backward compatible:

    - ``time`` comes from ``cfg.time_field``
    - ``value`` comes from ``cfg.value_field``

    In addition, all dataframe columns are exposed by their column names. This
    allows labels such as ``{hora:02.0f}``, ``{cta:.0f}``, or
    ``{data_hora:%H:%M}`` when those columns exist in the processed layer.
    """
    context: dict[str, Any] = {}

    for key, value in row.items():
        context[str(key)] = _coerce_datetime(value)

    context["time"] = (
        context.get(cfg.time_field, "")
        if cfg.time_field
        else ""
    )
    context["value"] = (
        context.get(cfg.value_field, "")
        if cfg.value_field
        else ""
    )

    return context


def draw_annotate(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> None:
    """
    Render periodic text annotations.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    layer : ProcessedDataLayer
        Processed runtime layer.
    cfg : AnnotateRenderConfig
        Rendering configuration.
    """
    if cfg.every <= 0:
        return

    order_by = None
    if layer.config.temporal is not None:
        order_by = layer.config.temporal.time_col

    df = layer.ordered_frame(order_by).reset_index(drop=True)

    for i, row in df.iterrows():
        if i % cfg.every != 0:
            continue

        context = _build_annotation_context(row, cfg)
        label = cfg.template.format(**context)

        ax.text(
            row["_T"] + cfg.dx,
            row["_W"] + cfg.dy,
            label,
            fontsize=cfg.fontsize,
            fontweight=cfg.fontweight,
            color=cfg.color,
            zorder=cfg.zorder,
        )
