import textwrap

from psychchart import PsychChart, load_chart_config


def _render_config(tmp_path, yaml_content: str):
    cfg = tmp_path / "operational_overlay.yaml"
    cfg.write_text(textwrap.dedent(yaml_content), encoding="utf-8")

    data = load_chart_config(cfg)
    chart = PsychChart(**data)
    ax = chart.draw()

    assert ax is not None
    assert len(ax.collections) > 0
    return data, chart, ax


def test_operational_overlay_smoke_with_explicit_profile(tmp_path):
    """Validate and render a minimal operational overlay configuration."""
    yaml_content = """
    profile: default_si

    chart:
      t_min: 10
      t_max: 42
      y_min: 0.0
      y_max: 0.032
      pressure: 101325
      output: operational_overlay_smoke.png

    operational_profiles:
      dairy_cooling_default:
        name: dairy_cooling_default

        itu_classes:
          - {name: I0, min: null, max: 72.0}
          - {name: I1, min: 72.0, max: 78.0}
          - {name: I2, min: 78.0, max: 84.0}
          - {name: I3, min: 84.0, max: 90.0}
          - {name: I4, min: 90.0, max: null}

        humidity_classes:
          - {name: H0, min: 0.00, max: 0.60}
          - {name: H1, min: 0.60, max: 0.75}
          - {name: H2, min: 0.75, max: 1.01}

        load_classes:
          - {name: A0, min: 0.000, max: 0.005, floor_action: O0, representative: 0.0025}
          - {name: A1, min: 0.005, max: 0.010, floor_action: O1, representative: 0.0075}
          - {name: A2, min: 0.010, max: 0.015, floor_action: O2, representative: 0.0125}
          - {name: A3, min: 0.015, max: 0.025, floor_action: O3, representative: 0.0200}
          - {name: A4, min: 0.025, max: null, floor_action: O5, representative: 0.0300}

        base_matrix:
          I0: {H0: O0, H1: O0, H2: O0}
          I1: {H0: O1, H1: O2, H2: O3}
          I2: {H0: O2, H1: O3, H2: O4}
          I3: {H0: O3, H1: O4, H2: O4}
          I4: {H0: O5, H1: O5, H2: O5}

        action_styles:
          O0: {label: "Monitoramento", facecolor: "#d9f0d3"}
          O1: {label: "Ventilação básica", facecolor: "#78c679"}
          O2: {label: "Ventilação reforçada", facecolor: "#ffd92f"}
          O3: {label: "Ventilação + aspersão", facecolor: "#fdae61"}
          O4: {label: "Resfriamento máximo", facecolor: "#f46d43"}
          O5: {label: "Emergência", facecolor: "#d73027"}

        modifiers:
          high_temp_humidity:
            temp_ge: 30.0
            rh_ge: 0.75
            add_levels: 1

    operational_overlays:
      - profile: dairy_cooling_default
        load_class: A2
        trend: steady
        alpha: 0.15
        n_t: 50
        n_rh: 40
        show_boundaries: true
    """

    data, _, _ = _render_config(tmp_path, yaml_content)

    assert "operational_profiles" in data
    assert "operational_overlays" in data
    assert data["operational_overlays"][0].load_class == "A2"


def test_operational_overlay_uses_default_dairy_profile(tmp_path):
    """Render an operational overlay using only the built-in dairy profile."""
    yaml_content = """
    profile: default_si

    chart:
      t_min: 10
      t_max: 42
      y_min: 0.0
      y_max: 0.032
      pressure: 101325
      output: operational_overlay_default_profile.png

    operational_overlays:
      - load_class: A2
        trend: steady
        alpha: 0.15
        n_t: 50
        n_rh: 40
        show_boundaries: true
    """

    data, _, _ = _render_config(tmp_path, yaml_content)

    assert "dairy_cooling_default" in data["operational_profiles"]
    assert data["operational_overlays"][0].profile == "dairy_cooling_default"
    assert data["operational_overlays"][0].load_class == "A2"
