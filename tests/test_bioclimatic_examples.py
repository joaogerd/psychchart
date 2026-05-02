from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from psychchart import PsychChart, load_chart_config

ROOT = Path(__file__).resolve().parents[1]

VALIDATED_EXAMPLES = [
    "examples/example_points.yaml",
    "examples/example_scatter.yaml",
    "examples/example_density.yaml",
    "examples/example_scalar_field.yaml",
    "examples/example_path.yaml",
    "examples/example_annotate.yaml",
    "examples/example_path_scatter_annotate.yaml",
    "examples/example_mixed.yaml",
    "examples/path_basic.yaml",
    "examples/path_colored_cta.yaml",
    "examples/path_scatter_annotate_cta.yaml",
    "examples/thermal_trajectory_classified.yaml",
    "examples/bovinos_racas.yaml",
    "examples/bovine_bioclimatic_final_azevedo.yaml",
    "examples/itu_field_labels.yaml",
    "examples/operational_overlay_minimal.yaml",
]


def render_example(relative_path: str):
    data = load_chart_config(ROOT / relative_path)
    chart = PsychChart(**data)
    ax = chart.draw()
    try:
        assert ax is not None
        assert len(ax.collections) > 0 or len(ax.lines) > 0 or len(ax.texts) > 0
    finally:
        plt.close(chart.fig)


@pytest.mark.parametrize("relative_path", VALIDATED_EXAMPLES)
def test_validated_yaml_example_smoke(relative_path):
    render_example(relative_path)
