import matplotlib.pyplot as plt

from psychchart import PsychChart, load_chart_config
from psychchart.config import AppConfig, InterventionZonesConfig


def test_app_config_accepts_intervention_zones():
    cfg = AppConfig.model_validate(
        {
            "chart": {
                "t_min": 10,
                "t_max": 45,
                "y_min": 0.0,
                "y_max": 0.035,
                "pressure": 101325,
                "xlabel": "Dry-bulb temperature (°C)",
                "ylabel": "Humidity ratio (kg/kg)",
                "output": "intervention_zones_test.png",
                "dpi": 150,
            },
            "intervention_zones": {
                "enabled": True,
                "rules": [
                    {
                        "name": "ventilation",
                        "label": "Ventilation",
                        "when": {"t_gte": 28, "w_lt": 0.020},
                        "vector": [-3.0, 0.0],
                    }
                ],
            },
        }
    )

    assert isinstance(cfg.intervention_zones, InterventionZonesConfig)
    payload = cfg.to_runtime_payload()
    assert payload["intervention_zones"] is cfg.intervention_zones


def test_intervention_zones_yaml_render_smoke():
    data = load_chart_config("examples/intervention_zones_minimal.yaml")
    chart = PsychChart(**data)

    try:
        chart.draw()
        text_values = {text.get_text() for text in chart.ax.texts}
        assert "Ventilation" in text_values
        assert "Reduce humidity" in text_values
        assert "Avoid evaporative\nhot and humid" in text_values
    finally:
        plt.close(chart.fig)
