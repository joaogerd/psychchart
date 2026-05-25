from __future__ import annotations

import pytest

from psychchart.config.app import AppConfig


def _chart():
    return {
        "t_min": 0.0,
        "t_max": 45.0,
        "pressure": 101325.0,
        "xlabel": "Temperature",
        "ylabel": "Humidity ratio",
        "output": "chart.png",
        "dpi": 100,
    }


def test_legacy_temporal_overlay_is_synthesized_as_data_layer():
    cfg = AppConfig.model_validate(
        {
            "chart": _chart(),
            "temporal_overlays": [
                {
                    "type": "CTA",
                    "data": "trajectory.csv",
                    "t_col": "temperature",
                    "rh_col": "relative_humidity",
                    "time_col": "hour",
                    "cta_col": "cta_accumulated",
                    "annotation_template": "{time}h\nCTA={cta:.0f}",
                }
            ],
        }
    )

    assert len(cfg.data_layers) == 1
    layer = cfg.data_layers[0]

    assert layer.data == "trajectory.csv"
    assert layer.format == "csv"
    assert layer.projection.t_col == "temperature"
    assert layer.projection.rh_col == "relative_humidity"
    assert layer.temporal is not None
    assert layer.temporal.time_col == "hour"

    assert len(layer.fields) == 1
    assert layer.fields[0].name == "CTA"
    assert layer.fields[0].col == "cta_accumulated"

    render_types = [item.type for item in layer.render]
    assert render_types == ["path", "scatter", "annotate"]

    path_cfg = layer.render[0]
    assert path_cfg.order_by == "hour"
    assert path_cfg.label == "CTA"

    scatter_cfg = layer.render[1]
    assert scatter_cfg.value == "CTA"

    annotate_cfg = layer.render[2]
    assert annotate_cfg.value_field == "CTA"
    assert annotate_cfg.template == "{time}h\nCTA={cta:.0f}"


def test_data_layers_take_precedence_over_legacy_temporal_overlays():
    cfg = AppConfig.model_validate(
        {
            "chart": _chart(),
            "data_layers": [
                {
                    "data": "canonical.csv",
                    "format": "csv",
                    "projection": {"t_col": "T", "rh_col": "RH"},
                    "render": [{"type": "points"}],
                }
            ],
            "temporal_overlays": [
                {
                    "type": "CTA",
                    "data": "legacy.csv",
                    "t_col": "temperature",
                    "rh_col": "relative_humidity",
                    "time_col": "hour",
                    "cta_col": "cta_accumulated",
                }
            ],
        }
    )

    assert len(cfg.data_layers) == 1
    assert cfg.data_layers[0].data == "canonical.csv"


def test_invalid_legacy_temporal_overlay_shape_fails_early():
    with pytest.raises(Exception):
        AppConfig.model_validate(
            {
                "chart": _chart(),
                "temporal_overlays": {"data": "trajectory.csv"},
            }
        )
