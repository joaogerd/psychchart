"""
Renderer for scatter representations of processed data layers.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from psychchart.data.layer_runtime import ProcessedDataLayer


def _resolve_order_by(layer: ProcessedDataLayer, cfg) -> str | None:
    if getattr(cfg, "order_by", None) is not None:
        return cfg.order_by

    temporal = getattr(layer.config, "temporal", None)
    if temporal is not None:
        return getattr(temporal, "time_col", None)

    return None


def _sample_frame(df, every: int | None):
    if every is None or every <= 1:
        return df.reset_index(drop=True)
    return df.iloc[::every].reset_index(drop=True)


def _colorbar_kwargs(cfg) -> dict:
    kwargs = {"label": cfg.colorbar_label or cfg.value}

    if cfg.colorbar_location is not None:
        kwargs["location"] = cfg.colorbar_location
    if cfg.colorbar_shrink is not None:
        kwargs["shrink"] = cfg.colorbar_shrink
    if cfg.colorbar_pad is not None:
        kwargs["pad"] = cfg.colorbar_pad
    if cfg.colorbar_aspect is not None:
        kwargs["aspect"] = cfg.colorbar_aspect
    if cfg.colorbar_fraction is not None:
        kwargs["fraction"] = cfg.colorbar_fraction
    if cfg.colorbar_ticks is not None:
        kwargs["ticks"] = cfg.colorbar_ticks

    return kwargs


def _style_colorbar(colorbar, cfg) -> None:
    if cfg.colorbar_labelpad is not None:
        colorbar.set_label(
            cfg.colorbar_label or cfg.value,
            labelpad=cfg.colorbar_labelpad,
            rotation=cfg.colorbar_label_rotation,
        )
    elif cfg.colorbar_label_rotation is not None:
        colorbar.set_label(
            cfg.colorbar_label or cfg.value,
            rotation=cfg.colorbar_label_rotation,
        )


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
    df = layer.ordered_frame(_resolve_order_by(layer, cfg))
    df = _sample_frame(df, getattr(cfg, "every", 1))

    if cfg.value is None:
        ax.scatter(
            df["_T"].to_numpy(),
            df["_W"].to_numpy(),
            color=cfg.color or "black",
            s=cfg.size,
            alpha=cfg.alpha,
            edgecolors=cfg.edgecolor,
            linewidths=cfg.edgewidth,
            zorder=cfg.zorder,
        )
        return

    if cfg.value not in df.columns:
        available = ", ".join(map(str, df.columns))
        raise KeyError(
            f"Scatter renderer requested value={cfg.value!r}, but this column "
            f"is not present in the processed dataframe. Available columns: {available}"
        )

    artist = ax.scatter(
        df["_T"].to_numpy(),
        df["_W"].to_numpy(),
        c=df[cfg.value].to_numpy(),
        cmap=cfg.cmap,
        s=cfg.size,
        alpha=cfg.alpha,
        edgecolors=cfg.edgecolor,
        linewidths=cfg.edgewidth,
        zorder=cfg.zorder,
    )

    if cfg.colorbar:
        colorbar = plt.colorbar(artist, ax=ax, **_colorbar_kwargs(cfg))
        _style_colorbar(colorbar, cfg)
