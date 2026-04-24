from __future__ import annotations

from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.collections import LineCollection

from psychchart.plot.data_renderers.path import draw_path


class DummyLayer:
    def __init__(self, df: pd.DataFrame, time_col: str | None = None):
        self._df = df
        self.config = SimpleNamespace(
            temporal=SimpleNamespace(time_col=time_col) if time_col else None
        )

    def ordered_frame(self, order_by: str | None):
        if order_by is None:
            return self._df.copy()
        return self._df.sort_values(order_by).copy()


def test_draw_plain_path_accepts_linestyle_and_label():
    df = pd.DataFrame(
        {
            "_T": [20.0, 22.0, 24.0],
            "_W": [0.010, 0.011, 0.012],
            "hour": [2, 0, 1],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    cfg = SimpleNamespace(
        order_by=None,
        color="black",
        alpha=0.9,
        linewidth=2.0,
        linestyle="--",
        label="Daily cycle",
        color_by=None,
        cmap="viridis",
        vmin=None,
        vmax=None,
        zorder=30,
    )

    fig, ax = plt.subplots()
    draw_path(ax, layer, cfg)

    assert len(ax.lines) == 1
    line = ax.lines[0]
    assert line.get_linestyle() == "--"
    assert line.get_label() == "Daily cycle"


def test_draw_colored_path_builds_linecollection():
    df = pd.DataFrame(
        {
            "_T": [20.0, 22.0, 24.0, 26.0],
            "_W": [0.010, 0.011, 0.012, 0.013],
            "hour": [0, 1, 2, 3],
            "cta": [1.0, 2.0, 4.0, 8.0],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    cfg = SimpleNamespace(
        order_by=None,
        color="black",
        alpha=0.9,
        linewidth=2.0,
        linestyle="-",
        label="CTA path",
        color_by="cta",
        cmap="inferno",
        vmin=0.0,
        vmax=10.0,
        zorder=30,
    )

    fig, ax = plt.subplots()
    draw_path(ax, layer, cfg)

    collections = [c for c in ax.collections if isinstance(c, LineCollection)]
    assert len(collections) == 1

    lc = collections[0]
    assert lc.get_label() == "CTA path"
    assert tuple(lc.get_clim()) == (0.0, 10.0)

    arr = lc.get_array()
    assert arr is not None
    assert len(arr) == 3
    assert list(arr) == [1.0, 2.0, 4.0]


def test_draw_colored_path_raises_keyerror_for_missing_column():
    df = pd.DataFrame(
        {
            "_T": [20.0, 22.0],
            "_W": [0.010, 0.011],
            "hour": [0, 1],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    cfg = SimpleNamespace(
        order_by=None,
        color="black",
        alpha=0.9,
        linewidth=2.0,
        linestyle="-",
        label=None,
        color_by="cta",
        cmap="inferno",
        vmin=None,
        vmax=None,
        zorder=30,
    )

    fig, ax = plt.subplots()

    with pytest.raises(KeyError, match="color_by='cta'|color_by=\"cta\""):
        draw_path(ax, layer, cfg)
