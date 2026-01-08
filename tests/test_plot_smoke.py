import matplotlib
matplotlib.use("Agg")  # backend sem GUI

from psychchart.plot import PsychChart
from psychchart.config import ChartConfig, IsoSet


def test_plot_smoke():
    cfg = ChartConfig(t_min=0, t_max=40)

    isolines = {
        "relative_humidity": IsoSet(
            name="relative_humidity",
            values=[0.3, 0.6, 0.9]
        )
    }

    chart = PsychChart(cfg, isolines=isolines)
    ax = chart.draw()

    # Verificações mínimas
    assert ax is not None
    assert ax.get_xlabel() != ""
    assert ax.get_ylabel() != ""

