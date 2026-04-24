"""
Renderer for scalar fields aggregated from processed data layers.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def draw_scalar_field(
    ax: Axes,
    layer: ProcessedDataLayer,
    cfg,
) -> None:
    """
    Render a scalar field projected from one processed layer.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Target axes.
    layer : ProcessedDataLayer
        Processed runtime layer.
    cfg : ScalarFieldRenderConfig
        Rendering configuration.
    """
    if layer.functional_observations is None:
        raise ValueError(
            "Scalar-field rendering requires at least one derived field "
            "in the data layer."
        )

    field = layer.functional_observations.to_scalar_field(
        cfg.value,
        bins=cfg.bins,
    )

    mesh = ax.pcolormesh(
        field.T_edges,
        field.W_edges,
        field.values,
        cmap=cfg.cmap,
        shading="auto",
        alpha=cfg.alpha,
        zorder=cfg.zorder,
    )

    if cfg.colorbar:
        plt.colorbar(mesh, ax=ax, label=field.name)
