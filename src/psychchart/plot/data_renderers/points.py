"""
Renderer for plain dataset points.
"""

from __future__ import annotations

from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def draw_points(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> None:
    """
    Render plain dataset points.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    layer : ProcessedDataLayer
        Processed runtime layer.
    cfg : PointsRenderConfig
        Rendering configuration.
    """
    ax.scatter(
        layer.T,
        layer.W,
        color=cfg.color,
        s=cfg.size,
        alpha=cfg.alpha,
        zorder=cfg.zorder,
    )
