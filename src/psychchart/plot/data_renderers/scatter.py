"""
Renderer for scatter representations of processed data layers.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def draw_scatter(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> None:
    """
    Render a scatter layer.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    layer : ProcessedDataLayer
        Processed runtime layer.
    cfg : ScatterRenderConfig
        Rendering configuration.
    """
    if cfg.value is None:
        ax.scatter(
            layer.T,
            layer.W,
            color=cfg.color or "black",
            s=cfg.size,
            alpha=cfg.alpha,
            edgecolors=cfg.edgecolor,
            linewidths=cfg.edgewidth,
            zorder=cfg.zorder,
        )
        return

    values = layer.get_array(cfg.value)

    artist = ax.scatter(
        layer.T,
        layer.W,
        c=values,
        cmap=cfg.cmap,
        s=cfg.size,
        alpha=cfg.alpha,
        edgecolors=cfg.edgecolor,
        linewidths=cfg.edgewidth,
        zorder=cfg.zorder,
    )

    if cfg.colorbar:
        plt.colorbar(artist, ax=ax, label=cfg.value)
