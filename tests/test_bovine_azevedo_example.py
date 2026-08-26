"""Smoke test for the dissertation-oriented Azevedo et al. (2005) chart."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from psychchart import PsychChart, load_chart_config


def test_bovine_azevedo_dissertation_chart_renders():
    config_path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "bovine_bioclimatic_final_azevedo.yaml"
    )

    cfg = load_chart_config(str(config_path))
    chart = PsychChart(**cfg)
    chart.draw()

    assert chart.fig is not None
    assert chart.ax is not None

    plt.close(chart.fig)
