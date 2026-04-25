from psychchart import load_chart_config
from psychchart.app.streamlit_app import (
    _compute_point_readout,
    _dump_yaml,
    _inject_readout_point,
    _load_yaml,
)
from psychchart.app.templates import TEMPLATES


def test_interactive_app_yaml_helpers_roundtrip():
    """The app YAML helpers must preserve mapping-based YAML documents."""
    data = _load_yaml("chart:\n  t_min: 10\n  t_max: 40\n")

    assert data["chart"]["t_min"] == 10
    assert data["chart"]["t_max"] == 40

    dumped = _dump_yaml(data)
    assert "chart:" in dumped
    assert "t_min: 10" in dumped


def test_interactive_templates_are_valid_configs(tmp_path):
    """Every built-in app template must be accepted by the config loader."""
    for name, yaml_text in TEMPLATES.items():
        path = tmp_path / f"{name.lower().replace(' ', '_')}.yaml"
        path.write_text(yaml_text, encoding="utf-8")

        data = load_chart_config(path)

        assert "cfg" in data
        assert data["cfg"].t_min < data["cfg"].t_max
        assert data["cfg"].pressure > 0


def test_point_readout_injection_adds_single_reference_point():
    """The interactive readout must be injected as one replaceable point."""
    base = {"chart": {"pressure": 101325}, "points": []}
    readout = _compute_point_readout(T=30.0, RH_pct=50.0, pressure=101325.0)

    first = _inject_readout_point(base, readout, enabled=True)
    second = _inject_readout_point(first, readout, enabled=True)

    readout_points = [
        point for point in second["points"] if point["label"].startswith("Readout:")
    ]

    assert len(readout_points) == 1
    assert readout_points[0]["t"] == 30.0
    assert readout_points[0]["rh"] == 0.5
    assert readout_points[0]["marker"] == "X"


def test_point_readout_injection_can_be_disabled():
    """Disabling the chart readout marker must remove prior readout points."""
    base = {"points": [{"t": 20, "rh": 0.5, "label": "Readout: old"}]}
    readout = _compute_point_readout(T=30.0, RH_pct=50.0, pressure=101325.0)

    result = _inject_readout_point(base, readout, enabled=False)

    assert result["points"] == []
