"""
Renderer for plain dataset points.
"""

from __future__ import annotations

from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def _sample_frame(df, every: int | None):
    if every is None or every <= 1:
        return df.reset_index(drop=True)
    return df.iloc[::every].reset_index(drop=True)


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
    df = _sample_frame(layer.frame, getattr(cfg, "every", 1))

    ax.scatter(
        df["_T"].to_numpy(),
        df["_W"].to_numpy(),
        color=cfg.color,
        s=cfg.size,
        alpha=cfg.alpha,
        zorder=cfg.zorder,
    )
