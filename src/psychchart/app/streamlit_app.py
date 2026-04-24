"""Streamlit interface for interactive psychChart exploration.

This module is intentionally optional. The scientific and rendering core remains
available through the Python API and CLI; the app is only a thin interactive
layer around the same YAML configuration model.
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import yaml

from psychchart import PsychChart, load_chart_config
from psychchart.indexes.itu import ITU
from psychchart.psychrometrics import Psychrometrics

from .templates import TEMPLATES


def _require_streamlit():
    """Import Streamlit with a clear error if the optional extra is missing."""
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised manually
        raise ModuleNotFoundError(
            "The interactive app requires Streamlit. Install it with: "
            "pip install -e .[app]"
        ) from exc
    return st


def _read_yaml_upload(uploaded_file) -> str | None:
    """Read an uploaded YAML file as UTF-8 text."""
    if uploaded_file is None:
        return None
    return uploaded_file.getvalue().decode("utf-8")


def _safe_yaml_load(text: str) -> dict[str, Any]:
    """Load YAML text into a mapping, returning an empty mapping for blanks."""
    data = yaml.safe_load(text) if text.strip() else {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise TypeError("The YAML document must be a mapping at the top level.")
    return data


def _safe_yaml_dump(data: dict[str, Any]) -> str:
    """Dump YAML using stable formatting suitable for copy/export."""
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def _set_nested(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    """Set a nested dictionary value, creating intermediate mappings."""
    cursor = data
    for key in path[:-1]:
        current = cursor.get(key)
        if not isinstance(current, dict):
            current = {}
            cursor[key] = current
        cursor = current
    cursor[path[-1]] = value


def _apply_sidebar_controls(st, data: dict[str, Any]) -> dict[str, Any]:
    """Apply high-level UI controls to a loaded YAML mapping."""
    edited = dict(data)
    chart = dict(edited.get("chart", {}))
    edited["chart"] = chart

    st.sidebar.subheader("Chart domain")
    t_min = st.sidebar.number_input("T min (°C)", value=float(chart.get("t_min", 10.0)))
    t_max = st.sidebar.number_input("T max (°C)", value=float(chart.get("t_max", 45.0)))
    y_min = st.sidebar.number_input("W min (kg/kg)", value=float(chart.get("y_min", 0.0)), format="%.4f")
    y_max = st.sidebar.number_input("W max (kg/kg)", value=float(chart.get("y_max", 0.035)), format="%.4f")
    pressure = st.sidebar.number_input("Pressure (Pa)", value=float(chart.get("pressure", 101325.0)), step=100.0)

    chart.update({"t_min": t_min, "t_max": t_max, "y_min": y_min, "y_max": y_max, "pressure": pressure})

    st.sidebar.subheader("Layers")
    show_rh = st.sidebar.checkbox("Relative humidity isolines", value="relative_humidity" in edited.get("isolines", {}))
    show_indexes = st.sidebar.checkbox("Thermal index layers", value=bool(edited.get("indexes")))
    show_zones = st.sidebar.checkbox("Zones / literature envelopes", value=bool(edited.get("zones")))
    show_data_layers = st.sidebar.checkbox("Data layers / trajectories", value=bool(edited.get("data_layers")))
    show_operational = st.sidebar.checkbox("Operational overlay", value=bool(edited.get("operational_overlays")))

    if not show_rh:
        isolines = dict(edited.get("isolines", {}))
        isolines.pop("relative_humidity", None)
        edited["isolines"] = isolines

    if not show_indexes:
        edited["indexes"] = []

    if not show_zones:
        edited["zones"] = []

    if not show_data_layers:
        edited["data_layers"] = []

    if not show_operational:
        edited["operational_overlays"] = []
    elif edited.get("operational_overlays"):
        st.sidebar.subheader("Operational state")
        load_class = st.sidebar.selectbox("Accumulated-load class", ["A0", "A1", "A2", "A3", "A4"], index=2)
        trend = st.sidebar.selectbox("Trend", ["falling", "steady", "rising"], index=1)
        alpha = st.sidebar.slider("Operational alpha", min_value=0.0, max_value=0.7, value=float(edited["operational_overlays"][0].get("alpha", 0.18)), step=0.01)
        overlay = dict(edited["operational_overlays"][0])
        overlay.update({"load_class": load_class, "trend": trend, "alpha": alpha})
        edited["operational_overlays"] = [overlay]

    st.sidebar.subheader("Index opacity")
    for item in edited.get("indexes", []) or []:
        render = item.get("render") or {}
        field = render.get("field")
        if isinstance(field, dict):
            field["alpha"] = st.sidebar.slider(
                f"{item.get('index', 'index')} field alpha",
                min_value=0.0,
                max_value=1.0,
                value=float(field.get("alpha", 0.45)),
                step=0.01,
            )

    return edited


def _render_yaml_to_figure(yaml_text: str):
    """Render a YAML document to a Matplotlib figure using the public API."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "interactive_config.yaml"
        config_path.write_text(yaml_text, encoding="utf-8")
        data = load_chart_config(config_path)
        chart = PsychChart(**data)
        chart.draw()
        return chart.fig


def _figure_to_png_bytes(fig) -> bytes:
    """Serialize a Matplotlib figure to PNG bytes."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()


def _point_readout(st, pressure: float) -> None:
    """Interactive single-point psychrometric and bioclimatic readout."""
    st.sidebar.subheader("Point readout")
    T = st.sidebar.number_input("Readout T (°C)", value=30.0, step=0.5)
    RH_percent = st.sidebar.number_input("Readout RH (%)", value=70.0, min_value=0.0, max_value=100.0, step=1.0)
    RH = RH_percent / 100.0

    W = Psychrometrics.humidity_ratio(T, RH, pressure)
    h = Psychrometrics.enthalpy(T, W)
    Tdp = Psychrometrics.dew_point_temperature(RH, T)
    itu = ITU.compute({"T": T, "RH": RH})

    st.metric("ITU", f"{itu:.1f}")
    st.caption(
        f"T={T:.1f} °C | RH={RH_percent:.0f}% | W={W:.5f} kg/kg | "
        f"h={h:.1f} kJ/kg dry air | Tdp={Tdp:.1f} °C"
    )


def main() -> None:  # pragma: no cover - interactive entry point
    """Run the Streamlit application."""
    st = _require_streamlit()

    st.set_page_config(
        page_title="psychChart interactive",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("psychChart interactive")
    st.caption("Interactive YAML-driven psychrometric and bovine bioclimatic chart explorer.")

    selected_template = st.sidebar.selectbox("Template", list(TEMPLATES), index=0)
    uploaded_yaml = st.sidebar.file_uploader("Load YAML configuration", type=["yaml", "yml"])

    if "yaml_text" not in st.session_state or st.sidebar.button("Reset from template"):
        st.session_state.yaml_text = TEMPLATES[selected_template]

    uploaded_text = _read_yaml_upload(uploaded_yaml)
    if uploaded_text is not None:
        st.session_state.yaml_text = uploaded_text

    raw_data = _safe_yaml_load(st.session_state.yaml_text)
    edited_data = _apply_sidebar_controls(st, raw_data)
    yaml_text = _safe_yaml_dump(edited_data)

    chart_pressure = float(edited_data.get("chart", {}).get("pressure", 101325.0))
    _point_readout(st, chart_pressure)

    left, right = st.columns([0.60, 0.40], gap="large")

    with right:
        st.subheader("YAML source of truth")
        yaml_text = st.text_area("Edit YAML", value=yaml_text, height=680)
        st.download_button(
            "Download YAML",
            data=yaml_text.encode("utf-8"),
            file_name="psychchart_interactive.yaml",
            mime="text/yaml",
        )

    with left:
        st.subheader("Chart preview")
        try:
            fig = _render_yaml_to_figure(yaml_text)
            st.pyplot(fig, clear_figure=False)
            png_bytes = _figure_to_png_bytes(fig)
            st.download_button(
                "Download PNG",
                data=png_bytes,
                file_name="psychchart_interactive.png",
                mime="image/png",
            )
            plt.close(fig)
        except Exception as exc:
            st.error(str(exc))
            st.exception(exc)


if __name__ == "__main__":  # pragma: no cover
    main()
