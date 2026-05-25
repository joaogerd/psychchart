from __future__ import annotations

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from psychchart.plot.data_renderers.annotate import draw_annotate


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


def test_annotate_formats_datetime_with_time_format():
    df = pd.DataFrame(
        {
            "_T": [20.0],
            "_W": [0.010],
            "data_hora": ["2025-11-08 15:00:00"],
            "CTA": [4.0],
        }
    )
    layer = DummyLayer(df, time_col="data_hora")
    cfg = SimpleNamespace(
        every=1,
        template="{time}\nCTA={value:.0f}",
        time_field="data_hora",
        value_field="CTA",
        time_format="%Hh",
        dx=0.0,
        dy=0.0,
        fontsize=8.0,
        fontweight="normal",
        color="black",
        zorder=30,
    )

    fig, ax = plt.subplots()
    draw_annotate(ax, layer, cfg)

    assert ax.texts[0].get_text() == "15h\nCTA=4"
