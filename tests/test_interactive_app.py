from psychchart import load_chart_config
from psychchart.app.streamlit_app import (
    _compute_point_readout,
    _dump_yaml,
    _inject_readout_point,
    _load_yaml,
    _select_template_yaml,
)
from psychchart.app.templates import TEMPLATES


class FakeSessionState(dict):
    """Small dict-like stand-in for Streamlit session_state."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class FakeSidebar:
    """Small stand-in for st.sidebar used by template-selection tests."""

    def __init__(self, button_value=False):
        self.button_value = button_value

    def button(self, _label):
        return self.button_value


class FakeStreamlit:
    """Minimal Streamlit facade for pure unit tests."""

    def __init__(self, button_value=False):
        self.session_state = FakeSessionState()
        self.sidebar = FakeSidebar(button_value=button_value)


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


def test_template_selection_refreshes_when_template_changes():
    """Changing the sidebar template must refresh the active YAML automatically."""
    st = FakeStreamlit()
    names = list(TEMPLATES)
    first_template = names[0]
    second_template = names[1]

    first_yaml = _select_template_yaml(st, first_template, uploaded_text=None)
    second_yaml = _select_template_yaml(st, second_template, uploaded_text=None)

    assert first_yaml == TEMPLATES[first_template]
    assert second_yaml == TEMPLATES[second_template]
    assert st.session_state.active_template == second_template


def test_template_selection_prefers_uploaded_yaml():
    """An uploaded YAML document must override the active template."""
    st = FakeStreamlit()
    uploaded = "chart:\n  t_min: 1\n  t_max: 2\n"

    selected = _select_template_yaml(st, list(TEMPLATES)[0], uploaded_text=uploaded)

    assert selected == uploaded
    assert st.session_state.yaml_text == uploaded
    assert st.session_state.active_template is None


def test_template_selection_reset_restores_current_template():
    """The reset button must restore the currently selected template."""
    st = FakeStreamlit(button_value=True)
    template_name = list(TEMPLATES)[0]
    st.session_state.yaml_text = "chart:\n  t_min: 99\n  t_max: 100\n"
    st.session_state.active_template = template_name

    selected = _select_template_yaml(st, template_name, uploaded_text=None)

    assert selected == TEMPLATES[template_name]
    assert st.session_state.yaml_text == TEMPLATES[template_name]


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
