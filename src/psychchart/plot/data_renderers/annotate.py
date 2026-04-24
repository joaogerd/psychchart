"""
Renderer for periodic annotations over processed data layers.
"""

from __future__ import annotations

from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


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

        context = {
            "time": row[cfg.time_field] if cfg.time_field else "",
            "value": row[cfg.value_field] if cfg.value_field else "",
        }

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
