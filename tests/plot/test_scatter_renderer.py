from __future__ import annotations

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from psychchart.plot.data_renderers.scatter import draw_scatter


class DummyLayer:
    def __init__(self, df: pd.DataFrame, time_col: str | None = None):
        self.frame = df
        self.config = SimpleNamespace(
            temporal=SimpleNamespace(time_col=time_col) if time_col else None
        )

    def ordered_frame(self, order_by: str | None):
        if order_by is None:
            return self.frame.copy()
        return self.frame.sort_values(order_by).copy()


def _cfg(**overrides):
    data = {
        "value": "cta",
        "order_by": None,
        "cmap": "viridis",
        "color": None,
        "size": 20.0,
        "alpha": 0.8,
        "edgecolor": "black",
        "edgewidth": 0.3,
        "every": 1,
        "colorbar": False,
        "colorbar_label": None,
        "colorbar_shrink": None,
        "colorbar_pad": None,
        "colorbar_aspect": None,
        "colorbar_ticks": None,
        "zorder": 45,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_draw_scatter_samples_after_temporal_ordering():
    df = pd.DataFrame(
        {
            "_T": [24.0, 20.0, 22.0, 26.0],
            "_W": [0.012, 0.010, 0.011, 0.013],
            "hour": [2, 0, 1, 3],
            "cta": [3.0, 1.0, 2.0, 4.0],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    fig, ax = plt.subplots()
    draw_scatter(ax, layer, _cfg(every=2))

    offsets = ax.collections[0].get_offsets()
    assert offsets.shape[0] == 2
    assert list(offsets[:, 0]) == [20.0, 24.0]


def test_draw_scatter_applies_colorbar_options():
    df = pd.DataFrame(
        {
            "_T": [20.0, 22.0, 24.0],
            "_W": [0.010, 0.011, 0.012],
            "hour": [0, 1, 2],
            "cta": [160.0, 180.0, 200.0],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    fig, ax = plt.subplots()
    draw_scatter(
        ax,
        layer,
        _cfg(
            colorbar=True,
            colorbar_label="CTA 19h",
            colorbar_shrink=0.8,
            colorbar_pad=0.02,
            colorbar_aspect=20,
            colorbar_ticks=[160, 180, 200],
        ),
    )

    assert len(fig.axes) == 2
    colorbar_ax = fig.axes[1]
    assert colorbar_ax.get_ylabel() == "CTA 19h"
    assert [tick.get_text() for tick in colorbar_ax.get_yticklabels()] == [
        "160",
        "180",
        "200",
    ]
