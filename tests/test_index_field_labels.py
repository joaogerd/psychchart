"""Tests for semantic labels rendered inside index field layers."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pytest

from psychchart import PsychChart, load_chart_config
from psychchart.psychrometrics import Psychrometrics


def _render_from_yaml(tmp_path, yaml: str) -> PsychChart:
    """Load a temporary YAML configuration and render it in memory."""
    cfg_path = tmp_path / "chart.yaml"
    cfg_path.write_text(yaml, encoding="utf-8")

    data = load_chart_config(cfg_path)
    chart = PsychChart(**data)
    chart.draw()
    return chart


def _text_by_label(chart: PsychChart, label: str):
    """Return the first Matplotlib text artist matching a label."""
    matches = [text for text in chart.ax.texts if text.get_text() == label]
    assert matches, f"Label {label!r} was not rendered inside the chart"
    return matches[0]


def test_field_render_config_accepts_label_options(tmp_path):
    """YAML label controls must be accepted by the typed configuration model."""
    yaml = """
chart:
  t_min: 10
  t_max: 42
  y_min: 0.0
  y_max: 0.035
  pressure: 101325

indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
        label_fontsize: 18
        label_color: "#222222"
        label_alpha: 0.90
        label_fontweight: bold
        label_rotation: -12
"""
    cfg_path = tmp_path / "chart.yaml"
    cfg_path.write_text(yaml, encoding="utf-8")

    data = load_chart_config(cfg_path)
    field_cfg = data["indexes"][0].render.field

    assert field_cfg.labels is True
    assert field_cfg.label_fontsize == 18
    assert field_cfg.label_color == "#222222"
    assert field_cfg.label_alpha == 0.90
    assert field_cfg.label_fontweight == "bold"
    assert field_cfg.label_rotation == -12


def test_automatic_index_field_labels_are_rendered(tmp_path):
    """Semantic labels should appear inside the index field when enabled."""
    yaml = """
chart:
  t_min: 10
  t_max: 42
  y_min: 0.0
  y_max: 0.035
  pressure: 101325

indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
        label_fontsize: 14
"""
    chart = _render_from_yaml(tmp_path, yaml)

    try:
        rendered = {text.get_text() for text in chart.ax.texts}
        assert {"Comfort", "Alert", "Stress"}.issubset(rendered)
    finally:
        plt.close(chart.fig)


def test_manual_index_field_label_positions_in_t_w_coordinates(tmp_path):
    """Manual T/W coordinates should be used directly as chart coordinates."""
    yaml = """
chart:
  t_min: 10
  t_max: 42
  y_min: 0.0
  y_max: 0.035
  pressure: 101325

indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
        label_fontsize: 14
        label_positions:
          - label: "Comfort"
            t: 16.0
            w: 0.006
            rotation: -5
          - label: "Alert"
            t: 25.0
            w: 0.012
            rotation: -10
          - label: "Stress"
            t: 34.0
            w: 0.020
            rotation: -15
"""
    chart = _render_from_yaml(tmp_path, yaml)

    try:
        comfort = _text_by_label(chart, "Comfort")
        alert = _text_by_label(chart, "Alert")
        stress = _text_by_label(chart, "Stress")

        assert comfort.get_position() == pytest.approx((16.0, 0.006))
        assert alert.get_position() == pytest.approx((25.0, 0.012))
        assert stress.get_position() == pytest.approx((34.0, 0.020))
        assert comfort.get_rotation() == pytest.approx(355.0)  # Matplotlib normalizes -5 degrees.
    finally:
        plt.close(chart.fig)


def test_manual_index_field_label_positions_in_t_rh_coordinates(tmp_path):
    """Manual T/RH coordinates should be converted to humidity ratio."""
    pressure = 101325
    yaml = """
chart:
  t_min: 10
  t_max: 42
  y_min: 0.0
  y_max: 0.035
  pressure: 101325

indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
        label_fontsize: 14
        label_positions:
          - label: "Comfort"
            t: 18.0
            rh: 60
          - label: "Alert"
            t: 26.0
            rh: 0.70
          - label: "Stress"
            t: 34.0
            rh: 80
"""
    chart = _render_from_yaml(tmp_path, yaml)

    try:
        comfort = _text_by_label(chart, "Comfort")
        alert = _text_by_label(chart, "Alert")
        stress = _text_by_label(chart, "Stress")

        expected_comfort_y = Psychrometrics.humidity_ratio(18.0, 0.60, pressure)
        expected_alert_y = Psychrometrics.humidity_ratio(26.0, 0.70, pressure)
        expected_stress_y = Psychrometrics.humidity_ratio(34.0, 0.80, pressure)

        assert comfort.get_position() == pytest.approx((18.0, expected_comfort_y))
        assert alert.get_position() == pytest.approx((26.0, expected_alert_y))
        assert stress.get_position() == pytest.approx((34.0, expected_stress_y))
    finally:
        plt.close(chart.fig)


def test_index_field_labels_are_not_rendered_when_disabled(tmp_path):
    """Semantic labels should remain hidden when render.field.labels is false."""
    yaml = """
chart:
  t_min: 10
  t_max: 42
  y_min: 0.0
  y_max: 0.035
  pressure: 101325

indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert", "Stress"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: false
"""
    chart = _render_from_yaml(tmp_path, yaml)

    try:
        rendered = {text.get_text() for text in chart.ax.texts}
        assert "Comfort" not in rendered
        assert "Alert" not in rendered
        assert "Stress" not in rendered
    finally:
        plt.close(chart.fig)


def test_inconsistent_index_field_labels_emit_warning_and_are_skipped(tmp_path):
    """Mismatched semantic labels should warn instead of failing silently."""
    yaml = """
chart:
  t_min: 10
  t_max: 42
  y_min: 0.0
  y_max: 0.035
  pressure: 101325

indexes:
  - index: ITU
    levels: [50, 63, 75, 79]
    colors: ["#1a9850", "#fee08b", "#fdae61"]
    labels: ["Comfort", "Alert"]
    render:
      field:
        alpha: 0.70
        colorbar: false
        labels: true
"""
    with pytest.warns(UserWarning, match="number of labels"):
        chart = _render_from_yaml(tmp_path, yaml)

    try:
        rendered = {text.get_text() for text in chart.ax.texts}
        assert "Comfort" not in rendered
        assert "Alert" not in rendered
    finally:
        plt.close(chart.fig)
