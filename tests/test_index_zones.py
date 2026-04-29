import matplotlib.pyplot as plt
import pytest

from psychchart import PsychChart, load_chart_config
from psychchart.config import AppConfig, IndexZone


def _minimal_chart_config():
    """Return the required ChartConfig fields for root-model validation tests."""
    return {
        "t_min": 10,
        "t_max": 45,
        "y_min": 0.0,
        "y_max": 0.035,
        "pressure": 101325,
        "xlabel": "Dry-bulb temperature (°C)",
        "ylabel": "Humidity ratio (kg/kg dry air)",
        "output": "index_zone_test.png",
        "dpi": 150,
    }


def test_index_zone_accepts_styling_and_internal_label_options():
    """IndexZone should validate the full style and label schema."""
    zone = IndexZone(
        index="ITU",
        name="comfort",
        range=(68, 72),
        facecolor="#A8E67A",
        edgecolor="#5B8F3A",
        linewidth=1.1,
        alpha=0.38,
        show_label=True,
        label="ITU",
        label_position="manual",
        label_t=25.5,
        label_rh=55,
        label_color="#2F3A2F",
        label_fontsize=12,
        label_fontweight="bold",
        label_rotation=72,
    )

    assert zone.range == (68, 72)
    assert zone.label_rh == pytest.approx(0.55)
    assert zone.facecolor == "#A8E67A"
    assert zone.show_label is True


def test_index_zone_rejects_invalid_interval_order():
    """IndexZone intervals must have lower < upper."""
    with pytest.raises(ValueError):
        IndexZone(index="ITU", name="invalid", range=(72, 68))


def test_index_zone_manual_label_requires_coordinates():
    """Manual label placement must be explicit and reproducible."""
    with pytest.raises(ValueError):
        IndexZone(
            index="ITU",
            name="comfort",
            range=(68, 72),
            show_label=True,
            label_position="manual",
            label_t=25.0,
        )


def test_app_config_accepts_labeled_index_zone():
    """Root configuration should accept labeled index-derived zones."""
    cfg = AppConfig.model_validate(
        {
            "chart": _minimal_chart_config(),
            "index_zones": [
                {
                    "index": "ITU",
                    "name": "ITU comfort zone",
                    "range": [68, 72],
                    "facecolor": "#A8E67A",
                    "edgecolor": "#5B8F3A",
                    "linewidth": 1.1,
                    "alpha": 0.38,
                    "show_label": True,
                    "label": "ITU",
                    "label_position": "auto",
                    "label_color": "#2F3A2F",
                    "label_fontsize": 12,
                    "label_fontweight": "bold",
                    "label_rotation": 72,
                }
            ],
        }
    )

    assert len(cfg.index_zones) == 1
    assert cfg.index_zones[0].label == "ITU"


def test_labeled_index_zone_render_smoke(tmp_path):
    """Rendering an index-zone fill with an internal label should not fail."""
    yaml = """
chart:
  t_min: 10
  t_max: 45
  y_min: 0.0
  y_max: 0.035
  output: index_zone_smoke.png

indexes:
  - index: ITU
    render:
      isolines:
        levels: [68, 72]
        color: "black"
        linewidth: 0.8
        label: true
        label_fmt: "ITU {value:.0f}"

index_zones:
  - index: ITU
    name: "ITU comfort zone"
    range: [68, 72]
    facecolor: "#A8E67A"
    edgecolor: "#5B8F3A"
    linewidth: 1.0
    alpha: 0.35
    show_label: true
    label: "ITU"
    label_position: auto
    label_color: "#2F3A2F"
    label_fontsize: 10
    label_fontweight: bold
    label_rotation: 70
"""
    cfg_file = tmp_path / "index_zone.yaml"
    cfg_file.write_text(yaml)

    data = load_chart_config(cfg_file)
    chart = PsychChart(**data)
    chart.draw()
    plt.close(chart.fig)
