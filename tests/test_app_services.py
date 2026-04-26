"""Tests for reusable interactive-application services."""

from __future__ import annotations

import pandas as pd
import pytest

from psychchart.app.services import (
    CsvLayerOptions,
    apply_csv_layer,
    build_csv_data_layer,
    build_report,
    compute_point_readout,
    dump_yaml,
    ensure_operational_overlay,
    inject_readout_point,
    is_empty_layer_value,
    layer_count,
    load_yaml_text,
)


def test_load_yaml_text_requires_mapping() -> None:
    """YAML documents used by the app must be top-level mappings."""
    assert load_yaml_text("chart:\n  t_min: 10\n") == {"chart": {"t_min": 10}}

    with pytest.raises(TypeError):
        load_yaml_text("- not\n- a\n- mapping\n")


def test_dump_yaml_round_trip() -> None:
    """Serialized YAML remains readable by the application service layer."""
    original = {"chart": {"t_min": 10, "t_max": 45}, "data_layers": []}
    rendered = dump_yaml(original)
    assert load_yaml_text(rendered) == original


def test_empty_layer_detection_and_counts() -> None:
    """Layer helpers provide stable semantics for empty sections."""
    assert is_empty_layer_value(None)
    assert is_empty_layer_value([])
    assert is_empty_layer_value({})
    assert not is_empty_layer_value([{"x": 1}])

    data = {"indexes": [{"index": "ITU"}], "isolines": {"relative_humidity": {}}}
    assert layer_count(data, "indexes") == 1
    assert layer_count(data, "isolines") == 1
    assert layer_count(data, "zones") == 0


def test_compute_point_readout_returns_physical_values() -> None:
    """Point readout computes consistent psychrometric quantities."""
    readout = compute_point_readout(T=30.0, RH_pct=50.0, pressure=101325.0)

    assert readout.T == 30.0
    assert readout.RH_pct == 50.0
    assert readout.RH == 0.5
    assert readout.W > 0.0
    assert readout.h > 0.0
    assert readout.ITU > 0.0


def test_inject_readout_point_replaces_previous_readout() -> None:
    """Only one dynamic readout point should be present in a config."""
    readout = compute_point_readout(T=30.0, RH_pct=50.0, pressure=101325.0)
    data = {
        "points": [
            {"label": "Permanent point", "t": 20.0, "rh": 0.5},
            {"label": "Readout: old", "t": 10.0, "rh": 0.8},
        ]
    }

    edited = inject_readout_point(data, readout, enabled=True)

    labels = [point["label"] for point in edited["points"]]
    assert labels[0] == "Permanent point"
    assert len([label for label in labels if label.startswith("Readout:")]) == 1


def test_ensure_operational_overlay_adds_default() -> None:
    """The default operational overlay is added only when missing."""
    data = {"operational_overlays": []}
    edited = ensure_operational_overlay(data)

    assert len(edited["operational_overlays"]) == 1
    assert edited["operational_overlays"][0]["load_class"] == "A2"


def test_build_csv_data_layer_scatter() -> None:
    """CSV uploads are converted to canonical data-layer configuration."""
    df = pd.DataFrame({"temp": [25.0, 26.0], "rh": [60.0, 65.0]})
    layer = build_csv_data_layer(df, CsvLayerOptions(t_col="temp", rh_col="rh"))

    assert layer["format"] == "csv"
    assert layer["projection"] == {"t_col": "temp", "rh_col": "rh", "rh_unit": "auto"}
    assert layer["render"][0]["type"] == "scatter"


def test_apply_csv_layer_replaces_or_appends() -> None:
    """CSV-derived layers can replace or append to existing data layers."""
    data = {"data_layers": [{"data": "old.csv"}]}
    layer = {"data": "new.csv"}

    replaced = apply_csv_layer(data, layer, replace_existing=True)
    appended = apply_csv_layer(data, layer, replace_existing=False)

    assert replaced["data_layers"] == [layer]
    assert appended["data_layers"] == [{"data": "old.csv"}, layer]


def test_build_report_contains_reproducibility_context() -> None:
    """The interactive report must document the active YAML source."""
    data = {"chart": {"t_min": 10, "t_max": 45, "pressure": 101325}}
    report = build_report(data, "chart:\n  t_min: 10\n")

    assert "psychChart interactive report" in report
    assert "Temperature range: 10 to 45" in report
    assert "```yaml" in report
