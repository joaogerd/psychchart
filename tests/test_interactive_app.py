from pathlib import Path

from psychchart import load_chart_config
from psychchart.app.streamlit_app import _dump_yaml, _load_yaml
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
