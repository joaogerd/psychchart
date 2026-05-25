from __future__ import annotations

from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

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


def _cfg(**overrides):
    data = {
        "every": 1,
        "template": "{time}h\nCTA={value:.0f}",
        "time_field": "hour",
        "value_field": "CTA",
        "dx": 0.0,
        "dy": 0.0,
        "fontsize": 8.0,
        "fontweight": "normal",
        "color": "black",
        "zorder": 30,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_annotate_supports_value_alias_and_temporal_ordering():
    df = pd.DataFrame(
        {
            "_T": [22.0, 20.0],
            "_W": [0.011, 0.010],
            "hour": [1, 0],
            "CTA": [12.0, 4.0],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    fig, ax = plt.subplots()
    draw_annotate(ax, layer, _cfg())

    assert [text.get_text() for text in ax.texts] == ["0h\nCTA=4", "1h\nCTA=12"]


def test_annotate_supports_legacy_cta_alias():
    df = pd.DataFrame(
        {
            "_T": [20.0],
            "_W": [0.010],
            "hour": [0],
            "CTA": [4.0],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    fig, ax = plt.subplots()
    draw_annotate(
        ax,
        layer,
        _cfg(template="{time}h\n(CTA:{cta:.0f})"),
    )

    assert ax.texts[0].get_text() == "0h\n(CTA:4)"


def test_annotate_reports_missing_template_field():
    df = pd.DataFrame(
        {
            "_T": [20.0],
            "_W": [0.010],
            "hour": [0],
            "CTA": [4.0],
        }
    )
    layer = DummyLayer(df, time_col="hour")

    fig, ax = plt.subplots()
    with pytest.raises(KeyError, match="unknown field"):
        draw_annotate(ax, layer, _cfg(template="{missing}"))
