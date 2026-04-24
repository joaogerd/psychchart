from pathlib import Path

import matplotlib.pyplot as plt

from psychchart import PsychChart, load_chart_config

ROOT = Path(__file__).resolve().parents[1]


def render_example(relative_path: str):
    data = load_chart_config(ROOT / relative_path)
    chart = PsychChart(**data)
    ax = chart.draw()
    assert ax is not None
    assert len(ax.collections) > 0
    plt.close(chart.fig)


def test_bovine_bioclimatic_final_azevedo_example_smoke():
    render_example("examples/bovine_bioclimatic_final_azevedo.yaml")


def test_thermal_trajectory_classified_example_smoke():
    render_example("examples/thermal_trajectory_classified.yaml")
